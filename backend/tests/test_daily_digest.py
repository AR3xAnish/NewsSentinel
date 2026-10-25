import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.models.models import Story, Article, NewsSource, StoryArticle
from app.services.telegram_service import TelegramService
from app.services.scheduler_service import scheduler_service
from app.main import app

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

def test_format_daily_digest_empty(test_db):
    tg = TelegramService()
    res = tg.format_daily_digest(test_db)
    assert res["stories_count"] == 0
    assert "DAILY AI NEWS INTELLIGENCE DIGEST" in res["message"]
    assert "No new news stories recorded today" in res["message"]

def test_format_daily_digest_with_stories(test_db):
    src = NewsSource(name="OpenAI Blog", url="https://openai.com/news/rss.xml", is_official=True)
    test_db.add(src)
    test_db.commit()

    art = Article(
        source_id=src.id,
        title="GPT-5 Launched Today",
        normalized_title="gpt-5 launched today",
        canonical_url="https://openai.com/index/gpt-5-launch",
        publisher="OpenAI",
        content_hash="hash_daily_1",
        published_at=datetime.now(timezone.utc)
    )
    test_db.add(art)
    test_db.commit()

    story = Story(
        story_uid="story_daily_1",
        headline="OpenAI Announces GPT-5 Frontier Model",
        verification_status="CORROBORATED",
        confidence_score=0.95,
        source_count=2,
        independent_source_count=2,
        summary_factual="OpenAI officially introduced GPT-5 with multimodal reasoning capabilities.",
        created_at=datetime.now(timezone.utc)
    )
    test_db.add(story)
    test_db.commit()

    sa = StoryArticle(story_id=story.id, article_id=art.id, is_primary=True)
    test_db.add(sa)
    test_db.commit()

    tg = TelegramService()
    digest = tg.format_daily_digest(test_db, max_stories=5)
    assert digest["stories_count"] == 1
    assert "OpenAI Announces GPT-5 Frontier Model" in digest["message"]
    assert "CORROBORATED" in digest["message"]
    assert "95%" in digest["message"]
    assert "OpenAI officially introduced" in digest["message"]
    assert "https://openai.com/index/gpt-5-launch" in digest["message"]

@pytest.mark.asyncio
async def test_send_daily_digest_unconfigured(test_db):
    tg = TelegramService()
    tg.bot_token = ""
    tg.chat_id = ""

    res = await tg.send_daily_digest(test_db)
    assert res["success"] is False
    assert "not configured" in res["error"]

@pytest.mark.asyncio
async def test_schedule_daily_digest_job():
    scheduler_service.start()
    scheduler_service.schedule_daily_digest_job("08:45", enabled=True)

    status = scheduler_service.get_schedule_status()
    assert status["daily_digest_enabled"] is True
    assert status["daily_digest_time"] == "08:45"
    assert status["next_daily_digest_run"] is not None

    # Test disable
    scheduler_service.schedule_daily_digest_job("08:45", enabled=False)
    status2 = scheduler_service.get_schedule_status()
    assert status2["daily_digest_enabled"] is False

def test_daily_digest_preview_endpoint():
    client = TestClient(app)
    response = client.get("/api/telegram/daily-digest/preview")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "DAILY AI NEWS INTELLIGENCE DIGEST" in data["message"]
