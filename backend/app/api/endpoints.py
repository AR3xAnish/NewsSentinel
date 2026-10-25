import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db
from app.models.models import (
    NewsSource, Article, Story, StoryArticle, Claim, Evidence,
    VerificationResult, SocialPost, NotificationDelivery, CollectionRun, ApplicationSetting
)
from app.schemas.schemas import (
    HealthResponse, OllamaHealthResponse, NewsSourceResponse, NewsSourceCreate,
    NewsSourceUpdate, ArticleResponse, StoryListItem, StoryDetailResponse,
    ClaimResponse, EvidenceResponse, SocialPostResponse, SocialPostUpdate,
    SocialPostGenerateRequest, CollectionRunResponse, CollectionTriggerRequest,
    SettingResponse, SettingUpdate, TelegramTestRequest, TelegramSendRequest,
    TelegramDailyDigestRequest, NotificationDeliveryResponse, StoryArticleResponse
)
from app.services.ollama_service import ollama_service
from app.services.rss_service import rss_service
from app.services.scheduler_service import scheduler_service
from app.services.claim_service import claim_service
from app.services.verification_service import verification_service
from app.services.summarization_service import summarization_service
from app.services.social_post_service import social_post_service
from app.services.telegram_service import telegram_service
from app.config import get_settings

router = APIRouter()
settings = get_settings()

# Health Endpoints
@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    ollama_stat = await ollama_service.check_health()
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        database="connected",
        ollama_connected=ollama_stat["connected"],
        scheduler_running=scheduler_service.scheduler.running,
        timestamp=datetime.now(timezone.utc)
    )

@router.get("/health/ollama", response_model=OllamaHealthResponse, tags=["Health"])
async def ollama_health():
    stat = await ollama_service.check_health()
    return OllamaHealthResponse(**stat)

# Dashboard Stats
@router.get("/stats", tags=["Dashboard"])
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_articles = db.query(Article).count()
    total_stories = db.query(Story).count()
    corroborated = db.query(Story).filter(Story.verification_status == "CORROBORATED").count()
    partially_corroborated = db.query(Story).filter(Story.verification_status == "PARTIALLY_CORROBORATED").count()
    conflicting = db.query(Story).filter(Story.verification_status == "CONFLICTING").count()
    unverified = db.query(Story).filter(Story.verification_status == "UNVERIFIED").count()
    insufficient = db.query(Story).filter(Story.verification_status == "INSUFFICIENT_EVIDENCE").count()

    last_run = db.query(CollectionRun).order_by(CollectionRun.started_at.desc()).first()

    return {
        "total_articles": total_articles,
        "total_stories": total_stories,
        "corroborated_stories": corroborated,
        "partially_corroborated_stories": partially_corroborated,
        "conflicting_stories": conflicting,
        "unverified_stories": unverified,
        "insufficient_evidence_stories": insufficient,
        "last_collection_time": last_run.finished_at or last_run.started_at if last_run else None,
        "last_run_status": last_run.status if last_run else "never_run",
    }

# Sources
@router.get("/sources", response_model=List[NewsSourceResponse], tags=["Sources"])
def list_sources(db: Session = Depends(get_db)):
    rss_service.seed_default_sources(db)
    return db.query(NewsSource).order_by(NewsSource.name).all()

@router.post("/sources", response_model=NewsSourceResponse, status_code=status.HTTP_201_CREATED, tags=["Sources"])
def create_source(source_in: NewsSourceCreate, db: Session = Depends(get_db)):
    existing = db.query(NewsSource).filter(NewsSource.url == source_in.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Source with this URL already exists.")
    
    src = NewsSource(**source_in.dict())
    db.add(src)
    db.commit()
    db.refresh(src)
    return src

@router.patch("/sources/{source_id}", response_model=NewsSourceResponse, tags=["Sources"])
def update_source(source_id: int, source_update: NewsSourceUpdate, db: Session = Depends(get_db)):
    src = db.query(NewsSource).filter(NewsSource.id == source_id).first()
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")
    
    for key, value in source_update.dict(exclude_unset=True).items():
        setattr(src, key, value)
    
    db.commit()
    db.refresh(src)
    return src

@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Sources"])
def delete_source(source_id: int, db: Session = Depends(get_db)):
    src = db.query(NewsSource).filter(NewsSource.id == source_id).first()
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(src)
    db.commit()
    return None

# Collection & Runs
@router.post("/collect", tags=["Collection"])
async def trigger_collection(req: Optional[CollectionTriggerRequest] = None):
    lookback = req.lookback_hours if req else None
    max_art = req.max_articles_per_feed if req else None
    res = await scheduler_service.execute_collection_pipeline(
        run_type="manual",
        lookback_hours=lookback,
        max_articles_per_feed=max_art
    )
    return res

@router.get("/runs", response_model=List[CollectionRunResponse], tags=["Collection"])
def list_collection_runs(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(CollectionRun).order_by(CollectionRun.started_at.desc()).limit(limit).all()

# News Stories
@router.get("/news", tags=["News"])
def list_news_stories(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    limit: int = 15,
    db: Session = Depends(get_db)
):
    query = db.query(Story)

    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(Story.verification_status == status_filter.upper())

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (Story.headline.ilike(search_pattern)) | 
            (Story.summary_factual.ilike(search_pattern))
        )

    total = query.count()
    offset = (page - 1) * limit
    stories = query.order_by(desc(Story.created_at)).offset(offset).limit(limit).all()

    items = []
    for s in stories:
        primary_sa = next((sa for sa in s.articles if sa.is_primary and sa.article), None)
        if not primary_sa and s.articles:
            primary_sa = s.articles[0]

        primary_article = primary_sa.article if primary_sa else None
        
        items.append({
            "id": s.id,
            "story_uid": s.story_uid,
            "headline": s.headline,
            "verification_status": s.verification_status,
            "confidence_score": s.confidence_score,
            "source_count": s.source_count,
            "independent_source_count": s.independent_source_count,
            "summary_factual": s.summary_factual,
            "primary_source_name": primary_article.publisher if primary_article else None,
            "primary_source_url": primary_article.canonical_url if primary_article else None,
            "earliest_published_at": primary_article.published_at if primary_article else None,
            "created_at": s.created_at,
            "ai_processed_at": s.ai_processed_at,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
    }

@router.get("/news/{story_id}", response_model=StoryDetailResponse, tags=["News"])
def get_story_detail(story_id: int, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Articles
    article_responses = []
    for sa in story.articles:
        if sa.article:
            article_responses.append(StoryArticleResponse(
                article_id=sa.article.id,
                title=sa.article.title,
                canonical_url=sa.article.canonical_url,
                publisher=sa.article.publisher,
                published_at=sa.article.published_at,
                is_primary=sa.is_primary,
                is_official=sa.article.source.is_official if sa.article.source else False
            ))

    # Claims and their evidence items
    claim_responses = []
    for c in story.claims:
        ev_items = []
        for ev in c.evidence_items:
            ev_items.append(EvidenceResponse(
                id=ev.id,
                claim_id=ev.claim_id,
                article_id=ev.article_id,
                publisher_name=ev.article.publisher if ev.article else None,
                article_url=ev.article.canonical_url if ev.article else None,
                verdict=ev.verdict,
                snippet=ev.snippet,
                material_discrepancy=ev.material_discrepancy,
                is_independent_source=ev.is_independent_source,
                confidence=ev.confidence
            ))

        src_article = c.source_article
        claim_responses.append(ClaimResponse(
            id=c.id,
            story_id=c.story_id,
            source_article_id=c.source_article_id,
            claim_text=c.claim_text,
            claim_type=c.claim_type,
            status=c.status,
            verification_notes=c.verification_notes,
            source_publisher=src_article.publisher if src_article else None,
            source_url=src_article.canonical_url if src_article else None,
            evidence_items=ev_items
        ))

    # Parse key facts
    facts = []
    if story.key_facts_dates:
        try:
            facts = json.loads(story.key_facts_dates)
        except Exception:
            pass

    return StoryDetailResponse(
        id=story.id,
        story_uid=story.story_uid,
        headline=story.headline,
        verification_status=story.verification_status,
        confidence_score=story.confidence_score,
        source_count=story.source_count,
        independent_source_count=story.independent_source_count,
        summary_factual=story.summary_factual,
        what_happened=story.what_happened,
        why_it_matters=story.why_it_matters,
        key_facts_dates=facts,
        what_remains_uncertain=story.what_remains_uncertain,
        verification_explanation=story.verification_explanation,
        ai_processed_at=story.ai_processed_at,
        created_at=story.created_at,
        articles=article_responses,
        claims=claim_responses,
    )

@router.post("/news/{story_id}/verify", tags=["News"])
async def trigger_story_verification(story_id: int, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    await claim_service.extract_claims_for_story(db, story)
    result = await verification_service.verify_story(db, story)
    return {"success": True, "verification_status": result.status, "confidence_score": result.confidence_score}

@router.post("/news/{story_id}/summarize", tags=["News"])
async def trigger_story_summary(story_id: int, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    updated = await summarization_service.generate_grounded_summary(db, story)
    return {"success": True, "headline": updated.headline, "summary": updated.summary_factual}

@router.get("/news/{story_id}/claims", response_model=List[ClaimResponse], tags=["News"])
def get_story_claims(story_id: int, db: Session = Depends(get_db)):
    claims = db.query(Claim).filter(Claim.story_id == story_id).all()
    res = []
    for c in claims:
        evs = [
            EvidenceResponse(
                id=ev.id,
                claim_id=ev.claim_id,
                article_id=ev.article_id,
                publisher_name=ev.article.publisher if ev.article else None,
                article_url=ev.article.canonical_url if ev.article else None,
                verdict=ev.verdict,
                snippet=ev.snippet,
                material_discrepancy=ev.material_discrepancy,
                is_independent_source=ev.is_independent_source,
                confidence=ev.confidence
            ) for ev in c.evidence_items
        ]
        res.append(ClaimResponse(
            id=c.id,
            story_id=c.story_id,
            source_article_id=c.source_article_id,
            claim_text=c.claim_text,
            claim_type=c.claim_type,
            status=c.status,
            verification_notes=c.verification_notes,
            source_publisher=c.source_article.publisher if c.source_article else None,
            source_url=c.source_article.canonical_url if c.source_article else None,
            evidence_items=evs
        ))
    return res

@router.get("/news/{story_id}/sources", response_model=List[ArticleResponse], tags=["News"])
def get_story_sources(story_id: int, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    articles = [sa.article for sa in story.articles if sa.article]
    return articles

# Social Studio
@router.get("/social-posts", response_model=List[SocialPostResponse], tags=["Social"])
def list_social_posts(
    story_id: Optional[int] = None,
    platform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SocialPost)
    if story_id:
        query = query.filter(SocialPost.story_id == story_id)
    if platform:
        query = query.filter(SocialPost.platform == platform.lower())
    return query.order_by(SocialPost.updated_at.desc()).all()

@router.post("/news/{story_id}/social-posts/generate", response_model=List[SocialPostResponse], tags=["Social"])
async def generate_social_posts(
    story_id: int,
    req: Optional[SocialPostGenerateRequest] = None,
    db: Session = Depends(get_db)
):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    platforms = req.platforms if req else ["linkedin", "x", "instagram"]
    posts = await social_post_service.generate_drafts_for_story(db, story, platforms)
    return posts

@router.patch("/social-posts/{post_id}", response_model=SocialPostResponse, tags=["Social"])
def update_social_post(post_id: int, post_in: SocialPostUpdate, db: Session = Depends(get_db)):
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post draft not found")

    post.content = post_in.content
    post.character_count = len(post_in.content)
    if post_in.status:
        post.status = post_in.status
    post.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(post)
    return post

@router.post("/social-posts/{post_id}/regenerate", response_model=SocialPostResponse, tags=["Social"])
async def regenerate_single_social_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post draft not found")

    story = post.story
    posts = await social_post_service.generate_drafts_for_story(db, story, [post.platform])
    return posts[0]

# Settings
@router.get("/settings", tags=["Settings"])
def get_app_settings(db: Session = Depends(get_db)):
    ollama_info = {
        "base_url": settings.OLLAMA_BASE_URL,
        "configured_model": settings.OLLAMA_MODEL,
        "temperature": settings.OLLAMA_TEMPERATURE,
    }
    telegram_info = telegram_service.get_configuration_status()
    schedule_stat = scheduler_service.get_schedule_status()
    scheduler_info = {
        "enabled": scheduler_service.scheduler.running and scheduler_service.is_enabled,
        "interval_minutes": scheduler_service.interval_minutes,
        "lookback_hours": settings.COLLECTION_LOOKBACK_HOURS,
        "max_articles_per_feed": settings.MAX_ARTICLES_PER_FEED,
        "next_collection_run": schedule_stat.get("next_collection_run"),
    }
    daily_digest_info = {
        "enabled": scheduler_service.daily_digest_enabled,
        "time": scheduler_service.daily_digest_time,
        "max_stories": scheduler_service.daily_digest_max_stories,
        "next_run": schedule_stat.get("next_daily_digest_run"),
    }

    # Stored dynamic settings from DB
    db_settings = {s.key: s.value for s in db.query(ApplicationSetting).all()}

    return {
        "ollama": ollama_info,
        "telegram": telegram_info,
        "scheduler": scheduler_info,
        "daily_digest": daily_digest_info,
        "custom": db_settings,
    }

@router.patch("/settings", tags=["Settings"])
def update_app_setting(update: SettingUpdate, key: str = Query(...), db: Session = Depends(get_db)):
    setting = db.query(ApplicationSetting).filter(ApplicationSetting.key == key).first()
    if setting:
        setting.value = update.value
        setting.updated_at = datetime.now(timezone.utc)
    else:
        setting = ApplicationSetting(key=key, value=update.value)
        db.add(setting)

    # Dynamic updates to in-memory settings & schedulers
    if key == "OLLAMA_MODEL":
        settings.OLLAMA_MODEL = update.value
        ollama_service.model = update.value
    elif key == "SCHEDULER_INTERVAL_MINUTES":
        try:
            val = int(update.value)
            scheduler_service.schedule_job(val)
        except ValueError:
            pass
    elif key == "DAILY_DIGEST_ENABLED":
        is_en = update.value.lower() in ("true", "1", "yes")
        scheduler_service.schedule_daily_digest_job(scheduler_service.daily_digest_time, enabled=is_en)
    elif key == "DAILY_DIGEST_TIME":
        scheduler_service.schedule_daily_digest_job(update.value, enabled=scheduler_service.daily_digest_enabled)
    elif key == "DAILY_DIGEST_MAX_STORIES":
        try:
            scheduler_service.daily_digest_max_stories = int(update.value)
        except ValueError:
            pass

    db.commit()
    return {"key": key, "value": update.value, "status": "updated"}

# Telegram
@router.post("/telegram/test", tags=["Telegram"])
async def test_telegram_delivery(req: TelegramTestRequest, db: Session = Depends(get_db)):
    res = await telegram_service.send_test_message(db=db, test_text=req.message)
    return res

@router.post("/telegram/send", tags=["Telegram"])
async def send_story_telegram(req: TelegramSendRequest, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == req.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    res = await telegram_service.send_story_summary(db=db, story=story, custom_note=req.custom_note)
    return res

@router.get("/telegram/daily-digest/preview", tags=["Telegram"])
def preview_daily_digest(max_stories: int = 5, db: Session = Depends(get_db)):
    """Previews the formatted Daily AI News Intelligence Digest message without sending it."""
    return telegram_service.format_daily_digest(db=db, max_stories=max_stories)

@router.post("/telegram/daily-digest", tags=["Telegram"])
async def send_daily_digest_now(
    req: Optional[TelegramDailyDigestRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Triggers immediate delivery of today's Daily AI News Intelligence Digest to Telegram.
    Optionally triggers a fresh collection run beforehand to ensure breaking news is captured.
    """
    force_collect = req.force_collect if req else True
    max_stories = req.max_stories if req else scheduler_service.daily_digest_max_stories
    custom_note = req.custom_note if req else None

    if force_collect:
        await scheduler_service.execute_collection_pipeline(run_type="daily_manual")

    res = await telegram_service.send_daily_digest(
        db=db,
        max_stories=max_stories,
        custom_note=custom_note
    )
    return res

@router.get("/deliveries", response_model=List[NotificationDeliveryResponse], tags=["Telegram"])
def list_notification_deliveries(limit: int = 25, db: Session = Depends(get_db)):
    return db.query(NotificationDelivery).order_by(NotificationDelivery.created_at.desc()).limit(limit).all()
