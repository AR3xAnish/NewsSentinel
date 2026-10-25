import pytest
from app.services.ollama_service import OllamaService
from app.services.telegram_service import TelegramService
from app.services.social_post_service import social_post_service
from app.models.models import Story, Article, NewsSource
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base

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

@pytest.mark.asyncio
async def test_ollama_offline_handling():
    # Use dummy unreachable port
    service = OllamaService()
    service.base_url = "http://127.0.0.1:59999"

    health = await service.check_health()
    assert health["connected"] is False
    assert health["model_installed"] is False
    assert "Could not connect to Ollama" in health["message"]

    # Calling generate_json should safely return None without throwing an unhandled exception
    res = await service.generate_json("System prompt", "User prompt")
    assert res is None

def test_telegram_unconfigured_state(test_db):
    tg = TelegramService()
    tg.bot_token = ""
    tg.chat_id = ""

    assert tg.is_configured() is False
    status = tg.get_configuration_status()
    assert status["configured"] is False
    assert "instructions" in status

@pytest.mark.asyncio
async def test_telegram_send_when_unconfigured(test_db):
    tg = TelegramService()
    tg.bot_token = ""
    tg.chat_id = ""

    res = await tg.send_test_message(test_db)
    assert res["success"] is False
    assert "not configured" in res["error"]

@pytest.mark.asyncio
async def test_social_post_x_character_limit(test_db):
    src = NewsSource(name="TechCrunch", url="https://techcrunch.com")
    test_db.add(src)
    test_db.commit()

    art = Article(
        source_id=src.id,
        title="Super Long Article Title Explaining Significant Breakthroughs In Large Language Model Architectures and Reasoning Capabilities Across Multiple Benchmarks",
        normalized_title="super long article title",
        canonical_url="https://techcrunch.com/long-title",
        publisher="TechCrunch",
        content_hash="h1",
    )
    test_db.add(art)
    test_db.commit()

    story = Story(
        story_uid="story-long",
        headline=art.title,
        primary_article_id=art.id,
        summary_factual="A very lengthy summary text that describes complex technical achievements in detail.",
    )
    test_db.add(story)
    test_db.commit()

    drafts = await social_post_service.generate_drafts_for_story(test_db, story, ["x", "linkedin", "instagram"])
    x_draft = next((d for d in drafts if d.platform == "x"), None)

    assert x_draft is not None
    assert x_draft.character_count <= 280
    assert len(x_draft.content) <= 280
