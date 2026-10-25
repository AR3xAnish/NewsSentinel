from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class NewsSource(Base):
    __tablename__ = "news_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    url = Column(String(512), unique=True, nullable=False, index=True)
    feed_type = Column(String(32), default="rss")
    category = Column(String(64), default="tech_media") # official_ai, research, tech_media
    is_enabled = Column(Boolean, default=True)
    is_official = Column(Boolean, default=False) # primary company/org source
    reliability_score = Column(Float, default=1.0) # default 1.0
    last_fetched_at = Column(DateTime, nullable=True)
    last_status = Column(String(32), default="pending") # success, error, pending
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("news_sources.id"), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    normalized_title = Column(String(512), nullable=False, index=True)
    canonical_url = Column(String(1024), unique=True, nullable=False, index=True)
    publisher = Column(String(128), nullable=False)
    author = Column(String(128), nullable=True)
    published_at = Column(DateTime, nullable=True, index=True)
    ingested_at = Column(DateTime, default=utc_now, index=True)
    feed_description = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=False, index=True)
    image_url = Column(String(1024), nullable=True)
    topic = Column(String(64), default="ai_news")
    extraction_status = Column(String(32), default="extracted") # extracted, rss_fallback, failed
    raw_metadata = Column(Text, nullable=True)

    source = relationship("NewsSource", back_populates="articles")
    story_associations = relationship("StoryArticle", back_populates="article", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="source_article")
    evidences = relationship("Evidence", back_populates="article")

class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    story_uid = Column(String(64), unique=True, nullable=False, index=True)
    headline = Column(String(512), nullable=False)
    primary_article_id = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    
    summary_factual = Column(Text, nullable=True)
    what_happened = Column(Text, nullable=True)
    why_it_matters = Column(Text, nullable=True)
    key_facts_dates = Column(Text, nullable=True) # JSON string
    what_remains_uncertain = Column(Text, nullable=True)
    
    # Verification statuses: CORROBORATED, PARTIALLY_CORROBORATED, CONFLICTING, UNVERIFIED, INSUFFICIENT_EVIDENCE
    verification_status = Column(String(32), default="UNVERIFIED", index=True)
    confidence_score = Column(Float, default=0.0)
    source_count = Column(Integer, default=1)
    independent_source_count = Column(Integer, default=1)
    verification_explanation = Column(Text, nullable=True)
    
    ai_processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    articles = relationship("StoryArticle", back_populates="story", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="story", cascade="all, delete-orphan")
    verification_results = relationship("VerificationResult", back_populates="story", cascade="all, delete-orphan")
    social_posts = relationship("SocialPost", back_populates="story", cascade="all, delete-orphan")
    notifications = relationship("NotificationDelivery", back_populates="story")

class StoryArticle(Base):
    __tablename__ = "story_articles"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    is_primary = Column(Boolean, default=False)
    relevance_score = Column(Float, default=1.0)

    story = relationship("Story", back_populates="articles")
    article = relationship("Article", back_populates="story_associations")

    __table_args__ = (UniqueConstraint("story_id", "article_id", name="uq_story_article"),)

class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    source_article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(32), default="factual") # factual, metric, date, statement
    status = Column(String(32), default="UNVERIFIED") # CORROBORATED, PARTIALLY_CORROBORATED, CONFLICTING, UNVERIFIED, INSUFFICIENT_EVIDENCE
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    story = relationship("Story", back_populates="claims")
    source_article = relationship("Article", back_populates="claims")
    evidence_items = relationship("Evidence", back_populates="claim", cascade="all, delete-orphan")

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    verdict = Column(String(32), nullable=False) # SUPPORTS, CONTRADICTS, INSUFFICIENT, NEUTRAL
    snippet = Column(Text, nullable=False)
    material_discrepancy = Column(Text, nullable=True) # specific date or numerical conflict
    is_independent_source = Column(Boolean, default=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=utc_now)

    claim = relationship("Claim", back_populates="evidence_items")
    article = relationship("Article", back_populates="evidences")

class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), nullable=False)
    confidence_score = Column(Float, default=0.0)
    explanation = Column(Text, nullable=False)
    independent_sources_count = Column(Integer, default=1)
    total_claims_count = Column(Integer, default=0)
    corroborated_claims_count = Column(Integer, default=0)
    conflicting_claims_count = Column(Integer, default=0)
    unverified_claims_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    story = relationship("Story", back_populates="verification_results")

class SocialPost(Base):
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(32), nullable=False, index=True) # linkedin, x, instagram
    content = Column(Text, nullable=False)
    hashtags = Column(String(512), nullable=True)
    character_count = Column(Integer, default=0)
    status = Column(String(32), default="DRAFT") # DRAFT, APPROVED, DELIVERED
    last_regenerated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    story = relationship("Story", back_populates="social_posts")

class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="SET NULL"), nullable=True, index=True)
    channel = Column(String(32), default="telegram")
    recipient_chat_id = Column(String(128), nullable=False)
    status = Column(String(32), default="PENDING") # SUCCESS, FAILED, PENDING
    message_preview = Column(Text, nullable=False)
    telegram_message_id = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    story = relationship("Story", back_populates="notifications")

class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_type = Column(String(32), default="manual") # manual, scheduled
    started_at = Column(DateTime, default=utc_now)
    finished_at = Column(DateTime, nullable=True)
    sources_attempted = Column(Integer, default=0)
    sources_successful = Column(Integer, default=0)
    articles_collected = Column(Integer, default=0)
    duplicates_detected = Column(Integer, default=0)
    stories_created = Column(Integer, default=0)
    status = Column(String(32), default="running") # running, success, partial_failure, failed
    error_log = Column(Text, nullable=True)

class ApplicationSetting(Base):
    __tablename__ = "application_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(String(256), nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
