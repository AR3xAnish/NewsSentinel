from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Health
class HealthResponse(BaseModel):
    status: str
    app_name: str
    database: str
    ollama_connected: bool
    scheduler_running: bool
    timestamp: datetime

class OllamaHealthResponse(BaseModel):
    connected: bool
    base_url: str
    configured_model: str
    model_installed: bool
    available_models: List[str] = []
    message: str

# News Source
class NewsSourceBase(BaseModel):
    name: str
    url: str
    feed_type: str = "rss"
    category: str = "tech_media"
    is_enabled: bool = True
    is_official: bool = False
    reliability_score: float = 1.0

class NewsSourceCreate(NewsSourceBase):
    pass

class NewsSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_official: Optional[bool] = None
    reliability_score: Optional[float] = None

class NewsSourceResponse(NewsSourceBase):
    id: int
    last_fetched_at: Optional[datetime] = None
    last_status: str
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Article
class ArticleResponse(BaseModel):
    id: int
    source_id: int
    title: str
    canonical_url: str
    publisher: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    ingested_at: datetime
    feed_description: Optional[str] = None
    extracted_text: Optional[str] = None
    image_url: Optional[str] = None
    topic: str
    extraction_status: str

    class Config:
        from_attributes = True

# Evidence
class EvidenceResponse(BaseModel):
    id: int
    claim_id: int
    article_id: int
    publisher_name: Optional[str] = None
    article_url: Optional[str] = None
    verdict: str  # SUPPORTS, CONTRADICTS, INSUFFICIENT, NEUTRAL
    snippet: str
    material_discrepancy: Optional[str] = None
    is_independent_source: bool = True
    confidence: float

    class Config:
        from_attributes = True

# Claim
class ClaimResponse(BaseModel):
    id: int
    story_id: int
    source_article_id: int
    claim_text: str
    claim_type: str
    status: str
    verification_notes: Optional[str] = None
    source_publisher: Optional[str] = None
    source_url: Optional[str] = None
    evidence_items: List[EvidenceResponse] = []

    class Config:
        from_attributes = True

# Story
class StoryArticleResponse(BaseModel):
    article_id: int
    title: str
    canonical_url: str
    publisher: str
    published_at: Optional[datetime] = None
    is_primary: bool
    is_official: bool

class StoryListItem(BaseModel):
    id: int
    story_uid: str
    headline: str
    verification_status: str
    confidence_score: float
    source_count: int
    independent_source_count: int
    summary_factual: Optional[str] = None
    primary_source_name: Optional[str] = None
    primary_source_url: Optional[str] = None
    earliest_published_at: Optional[datetime] = None
    created_at: datetime
    ai_processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StoryDetailResponse(BaseModel):
    id: int
    story_uid: str
    headline: str
    verification_status: str
    confidence_score: float
    source_count: int
    independent_source_count: int
    summary_factual: Optional[str] = None
    what_happened: Optional[str] = None
    why_it_matters: Optional[str] = None
    key_facts_dates: Optional[List[Dict[str, Any]]] = None
    what_remains_uncertain: Optional[str] = None
    verification_explanation: Optional[str] = None
    ai_processed_at: Optional[datetime] = None
    created_at: datetime
    articles: List[StoryArticleResponse] = []
    claims: List[ClaimResponse] = []

    class Config:
        from_attributes = True

# Social Post
class SocialPostResponse(BaseModel):
    id: int
    story_id: int
    platform: str
    content: str
    hashtags: Optional[str] = None
    character_count: int
    status: str
    last_regenerated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SocialPostUpdate(BaseModel):
    content: str
    status: Optional[str] = "DRAFT"

class SocialPostGenerateRequest(BaseModel):
    platforms: List[str] = ["linkedin", "x", "instagram"]

# Collection Run
class CollectionRunResponse(BaseModel):
    id: int
    run_type: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    sources_attempted: int
    sources_successful: int
    articles_collected: int
    duplicates_detected: int
    stories_created: int
    status: str
    error_log: Optional[str] = None

    class Config:
        from_attributes = True

class CollectionTriggerRequest(BaseModel):
    lookback_hours: Optional[int] = None
    max_articles_per_feed: Optional[int] = None

# Settings
class SettingResponse(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True

class SettingUpdate(BaseModel):
    value: str

# Telegram
class TelegramTestRequest(BaseModel):
    message: Optional[str] = "Test notification from YGF News Intelligence Agent."

class TelegramSendRequest(BaseModel):
    story_id: int
    custom_note: Optional[str] = None

class TelegramDailyDigestRequest(BaseModel):
    force_collect: bool = True
    max_stories: int = 5
    custom_note: Optional[str] = None

class NotificationDeliveryResponse(BaseModel):
    id: int
    story_id: Optional[int] = None
    channel: str
    recipient_chat_id: str
    status: str
    message_preview: str
    error_message: Optional[str] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Structured Ollama Extraction Models (Pydantic for LLM Outputs)
class ExtractedClaimItem(BaseModel):
    claim_text: str = Field(description="A concrete, checkable factual claim stated in the article")
    claim_type: str = Field(default="factual", description="Type: factual, metric, date, or statement")
    material_value: Optional[str] = Field(default=None, description="Specific number, date, version, or model mentioned")

class ClaimsExtractionResult(BaseModel):
    claims: List[ExtractedClaimItem] = []

class EvidenceAssessmentItem(BaseModel):
    claim_text: str
    verdict: str = Field(description="SUPPORTS, CONTRADICTS, INSUFFICIENT, or NEUTRAL")
    snippet: str = Field(description="Exact or near-exact quote/passage from this source text")
    discrepancy: Optional[str] = Field(default=None, description="Any conflicting date, numerical value, or scope")

class EvidenceAssessmentResult(BaseModel):
    assessments: List[EvidenceAssessmentItem] = []

class GroundedSummaryResult(BaseModel):
    headline: str
    summary_factual: str
    what_happened: str
    why_it_matters: str
    key_facts_dates: List[Dict[str, str]] = []
    what_remains_uncertain: str

class SocialDraftsResult(BaseModel):
    linkedin: str
    x: str
    instagram: str
    hashtags: str
