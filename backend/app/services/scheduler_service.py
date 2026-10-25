import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import CollectionRun, NewsSource, Story, ApplicationSetting
from app.services.rss_service import rss_service
from app.services.clustering_service import clustering_service
from app.services.claim_service import claim_service
from app.services.verification_service import verification_service
from app.services.summarization_service import summarization_service
from app.services.social_post_service import social_post_service
from app.services.telegram_service import telegram_service
from app.config import get_settings

settings = get_settings()

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._is_running_job = False
        self._lock = asyncio.Lock()
        self.interval_minutes = settings.SCHEDULER_INTERVAL_MINUTES
        self.is_enabled = settings.SCHEDULER_ENABLED
        self.daily_digest_enabled = settings.DAILY_DIGEST_ENABLED
        self.daily_digest_time = settings.DAILY_DIGEST_TIME
        self.daily_digest_max_stories = settings.DAILY_DIGEST_MAX_STORIES

    def start(self):
        """Initializes and starts the background scheduler if enabled."""
        if not self.scheduler.running:
            self.scheduler.start()
        
        # Schedule collection interval job if enabled
        if self.is_enabled:
            self.schedule_job(self.interval_minutes)
        
        # Schedule daily digest cron job if enabled
        if self.daily_digest_enabled:
            self.schedule_daily_digest_job(self.daily_digest_time, enabled=True)

    def shutdown(self):
        """Gracefully shuts down scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()

    def schedule_job(self, interval_minutes: int):
        """Adds or reschedules the automated collection job without clearing other jobs."""
        self.interval_minutes = interval_minutes
        try:
            self.scheduler.remove_job("automated_collection_job")
        except Exception:
            pass
        self.scheduler.add_job(
            self.run_scheduled_collection,
            "interval",
            minutes=interval_minutes,
            id="automated_collection_job"
        )

    def schedule_daily_digest_job(self, time_str: str = "09:00", enabled: bool = True):
        """Schedules or updates the daily Telegram news digest cron job."""
        self.daily_digest_time = time_str
        self.daily_digest_enabled = enabled

        try:
            self.scheduler.remove_job("daily_digest_job")
        except Exception:
            pass

        if not enabled:
            return

        try:
            parts = time_str.strip().split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        except Exception:
            hour = 9
            minute = 0

        self.scheduler.add_job(
            self.run_daily_digest,
            "cron",
            hour=hour,
            minute=minute,
            id="daily_digest_job",
            replace_existing=True
        )

    def get_schedule_status(self) -> Dict[str, Any]:
        """Returns details about running background jobs and their next execution times."""
        collection_job = self.scheduler.get_job("automated_collection_job") if self.scheduler.running else None
        daily_job = self.scheduler.get_job("daily_digest_job") if self.scheduler.running else None

        return {
            "scheduler_running": self.scheduler.running,
            "collection_enabled": self.is_enabled,
            "collection_interval_minutes": self.interval_minutes,
            "next_collection_run": str(collection_job.next_run_time) if collection_job and collection_job.next_run_time else None,
            "daily_digest_enabled": self.daily_digest_enabled,
            "daily_digest_time": self.daily_digest_time,
            "next_daily_digest_run": str(daily_job.next_run_time) if daily_job and daily_job.next_run_time else None,
            "telegram_configured": telegram_service.is_configured(),
        }

    async def run_scheduled_collection(self):
        """Triggered automatically by APScheduler."""
        await self.execute_collection_pipeline(run_type="scheduled")

    async def run_daily_digest(self):
        """Triggered daily by APScheduler cron: runs collection and delivers daily digest to Telegram."""
        # 1. Run fresh collection to ingest latest breaking news
        await self.execute_collection_pipeline(run_type="daily_scheduled")

        # 2. Dispatch consolidated daily digest to Telegram if configured
        if telegram_service.is_configured():
            db: Session = SessionLocal()
            try:
                await telegram_service.send_daily_digest(
                    db=db,
                    max_stories=self.daily_digest_max_stories,
                    custom_note="Daily Automated Dispatch"
                )
            except Exception as e:
                print(f"[Scheduler] Error delivering daily digest: {e}")
            finally:
                db.close()

    async def execute_collection_pipeline(
        self,
        run_type: str = "manual",
        lookback_hours: Optional[int] = None,
        max_articles_per_feed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes the complete end-to-end news intelligence pipeline:
        1. Ingest from active sources
        2. Deduplicate and extract
        3. Cluster into stories
        4. Extract claims
        5. Cross-validate claims
        6. Generate grounded summaries
        7. Generate platform social drafts
        """
        if self._is_running_job:
            return {
                "success": False,
                "error": "A collection run is currently in progress. Overlapping run prevented."
            }

        async with self._lock:
            self._is_running_job = True

            db: Session = SessionLocal()
            run_record = CollectionRun(
                run_type=run_type,
                started_at=datetime.now(timezone.utc),
                status="running"
            )
            db.add(run_record)
            db.commit()

            lookback = lookback_hours or settings.COLLECTION_LOOKBACK_HOURS
            max_art = max_articles_per_feed or settings.MAX_ARTICLES_PER_FEED

            total_attempted = 0
            total_successful = 0
            total_articles = 0
            total_duplicates = 0
            errors = []

            try:
                # Ensure default sources exist
                rss_service.seed_default_sources(db)

                # Fetch active sources
                sources = db.query(NewsSource).filter(NewsSource.is_enabled == True).all()
                total_attempted = len(sources)

                for src in sources:
                    res = await rss_service.ingest_source(
                        db=db,
                        source=src,
                        lookback_hours=lookback,
                        max_articles=max_art
                    )
                    if res["success"]:
                        total_successful += 1
                        total_articles += res["articles_added"]
                        total_duplicates += res["duplicates_found"]
                    else:
                        errors.append(f"Source [{src.name}]: {res.get('error')}")

                # Cluster newly collected articles into stories
                new_stories_count = clustering_service.cluster_articles(db)
                run_record.stories_created = new_stories_count

                # Process AI pipeline on newly created or pending stories
                pending_stories = db.query(Story).filter(Story.ai_processed_at.is_(None)).all()
                for story in pending_stories:
                    try:
                        # 1. Extract claims
                        await claim_service.extract_claims_for_story(db, story)
                        # 2. Cross-validate evidence
                        await verification_service.verify_story(db, story)
                        # 3. Grounded summary
                        await summarization_service.generate_grounded_summary(db, story)
                        # 4. Social drafts
                        await social_post_service.generate_drafts_for_story(db, story)

                        # 5. Optional automated Telegram delivery for newly corroborated stories on scheduled runs
                        if run_type == "scheduled" and telegram_service.is_configured():
                            auto_tg = db.query(ApplicationSetting).filter(ApplicationSetting.key == "TELEGRAM_AUTO_DISPATCH").first()
                            is_auto_enabled = auto_tg.value.lower() == "true" if auto_tg else False
                            if is_auto_enabled and story.verification_status in ("CORROBORATED", "PARTIALLY_CORROBORATED"):
                                await telegram_service.send_story_summary(db, story, custom_note="Automated Scheduled Alert")
                    except Exception as story_err:
                        errors.append(f"Story [{story.id}] processing: {str(story_err)}")

                # Complete run record
                run_record.finished_at = datetime.now(timezone.utc)
                run_record.sources_attempted = total_attempted
                run_record.sources_successful = total_successful
                run_record.articles_collected = total_articles
                run_record.duplicates_detected = total_duplicates
                run_record.status = "success" if not errors else ("partial_failure" if total_successful > 0 else "failed")
                run_record.error_log = "\n".join(errors) if errors else None
                db.commit()

                return {
                    "success": True,
                    "run_id": run_record.id,
                    "articles_collected": total_articles,
                    "duplicates_detected": total_duplicates,
                    "stories_created": new_stories_count,
                    "errors": errors
                }

            except Exception as e:
                db.rollback()
                run_record.finished_at = datetime.now(timezone.utc)
                run_record.status = "failed"
                run_record.error_log = f"Fatal run error: {str(e)}"
                db.commit()
                return {"success": False, "error": str(e)}

            finally:
                db.close()
                self._is_running_job = False

scheduler_service = SchedulerService()
