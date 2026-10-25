import feedparser
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import NewsSource, Article, CollectionRun
from app.services.article_service import article_service
from app.services.deduplication_service import deduplication_service
from app.utils.url_utils import normalize_url, normalize_title, generate_content_hash
from app.utils.date_utils import safe_parse_date, is_within_lookback
from app.utils.security import validate_url_safe, sanitize_html_text
from app.config import get_settings

settings = get_settings()

DEFAULT_NEWS_SOURCES = [
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "feed_type": "rss",
        "category": "tech_media",
        "is_official": False,
        "reliability_score": 0.9,
    },
    {
        "name": "Ars Technica AI & Tech",
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "feed_type": "rss",
        "category": "tech_media",
        "is_official": False,
        "reliability_score": 0.95,
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "feed_type": "rss",
        "category": "tech_media",
        "is_official": False,
        "reliability_score": 0.88,
    },
    {
        "name": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/feed/",
        "feed_type": "rss",
        "category": "research",
        "is_official": False,
        "reliability_score": 0.95,
    },
    {
        "name": "OpenAI Official Blog",
        "url": "https://openai.com/news/rss.xml",
        "feed_type": "rss",
        "category": "official_ai",
        "is_official": True,
        "reliability_score": 0.98,
    },
    {
        "name": "Google Research & AI",
        "url": "https://blog.google/technology/ai/rss/",
        "feed_type": "rss",
        "category": "official_ai",
        "is_official": True,
        "reliability_score": 0.98,
    },
    {
        "name": "ArXiv Computer Science AI",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "feed_type": "rss",
        "category": "research",
        "is_official": False,
        "reliability_score": 0.92,
    },
]

class RSSService:
    def seed_default_sources(self, db: Session) -> None:
        """Seeds default AI and tech news sources if the database table is empty."""
        count = db.query(NewsSource).count()
        if count == 0:
            for s_data in DEFAULT_NEWS_SOURCES:
                source = NewsSource(
                    name=s_data["name"],
                    url=s_data["url"],
                    feed_type=s_data["feed_type"],
                    category=s_data["category"],
                    is_enabled=True,
                    is_official=s_data["is_official"],
                    reliability_score=s_data["reliability_score"],
                    last_status="pending",
                )
                db.add(source)
            db.commit()

    async def fetch_feed_entries(self, source_url: str) -> List[Dict[str, Any]]:
        """Safely fetches and parses an RSS or Atom feed."""
        is_safe, msg = validate_url_safe(source_url)
        if not is_safe:
            raise ValueError(f"SSRF Protection: {msg}")

        headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9",
        }

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = await client.get(source_url, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code} returned when fetching feed")

            parsed = feedparser.parse(resp.text)
            if parsed.bozo and not parsed.entries:
                raise RuntimeError(f"Malformed XML feed: {getattr(parsed, 'bozo_exception', 'unknown error')}")

            entries = []
            for entry in parsed.entries:
                raw_url = getattr(entry, "link", "")
                title = getattr(entry, "title", "").strip()
                if not raw_url or not title:
                    continue

                published_raw = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None) or getattr(entry, "published", None) or getattr(entry, "pubDate", None)
                published_at = safe_parse_date(published_raw)

                author = getattr(entry, "author", None)
                summary = getattr(entry, "summary", "") or getattr(entry, "description", "")

                entries.append({
                    "raw_url": raw_url,
                    "title": title,
                    "published_at": published_at,
                    "author": author,
                    "summary": sanitize_html_text(summary),
                })

            return entries

    async def ingest_source(
        self,
        db: Session,
        source: NewsSource,
        lookback_hours: int = 48,
        max_articles: int = 10
    ) -> Dict[str, Any]:
        """
        Ingests articles from a single source.
        Applies SSRF checks, URL normalization, deduplication, and extraction.
        """
        articles_added = 0
        duplicates_found = 0
        now = datetime.now(timezone.utc)

        try:
            entries = await self.fetch_feed_entries(source.url)
            source.last_fetched_at = now
            source.last_status = "success"
            source.last_error = None
            db.commit()
        except Exception as e:
            source.last_fetched_at = now
            source.last_status = "error"
            source.last_error = str(e)[:500]
            db.commit()
            return {
                "success": False,
                "articles_added": 0,
                "duplicates_found": 0,
                "error": str(e)
            }

        collected_this_source = 0
        for entry in entries:
            if collected_this_source >= max_articles:
                break

            # Lookback filter
            if not is_within_lookback(entry["published_at"], lookback_hours):
                continue

            # Deduplication
            is_dup, reason = deduplication_service.is_duplicate(db, entry["raw_url"], entry["title"])
            if is_dup:
                duplicates_found += 1
                continue

            canonical_url = normalize_url(entry["raw_url"])
            normalized_title = normalize_title(entry["title"])
            content_hash = generate_content_hash(normalized_title, entry["summary"])

            # Extract full article content or fallback to RSS summary
            extraction = await article_service.extract_article_content(
                url=canonical_url,
                fallback_description=entry["summary"]
            )

            article = Article(
                source_id=source.id,
                title=entry["title"],
                normalized_title=normalized_title,
                canonical_url=canonical_url,
                publisher=source.name,
                author=entry["author"],
                published_at=entry["published_at"],
                ingested_at=now,
                feed_description=entry["summary"],
                extracted_text=extraction["extracted_text"],
                content_hash=content_hash,
                image_url=extraction["image_url"],
                topic="ai_news",
                extraction_status=extraction["extraction_status"],
            )

            db.add(article)
            db.flush()
            articles_added += 1
            collected_this_source += 1

        db.commit()
        return {
            "success": True,
            "articles_added": articles_added,
            "duplicates_found": duplicates_found,
            "error": None
        }

rss_service = RSSService()
