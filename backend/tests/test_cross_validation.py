import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.models import NewsSource, Article, Story, StoryArticle, Claim, Evidence
from app.services.verification_service import verification_service
from app.services.claim_service import claim_service

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
async def test_single_source_story_classified_insufficient_evidence(test_db):
    src = NewsSource(name="TechCrunch", url="https://techcrunch.com/feed")
    test_db.add(src)
    test_db.commit()

    art = Article(
        source_id=src.id,
        title="Startup XYZ raises $50M in Series B",
        normalized_title="startup xyz raises 50m in series b",
        canonical_url="https://techcrunch.com/startup-xyz-50m",
        publisher="TechCrunch",
        extracted_text="Startup XYZ announced today it raised $50M in Series B funding led by Tech Ventures.",
        content_hash="hash1",
    )
    test_db.add(art)
    test_db.commit()

    story = Story(
        story_uid="story-single-src",
        headline="Startup XYZ raises $50M in Series B",
        primary_article_id=art.id,
        source_count=1,
        independent_source_count=1,
    )
    test_db.add(story)
    test_db.flush()

    sa = StoryArticle(story_id=story.id, article_id=art.id, is_primary=True)
    test_db.add(sa)
    test_db.commit()

    # Extract claims
    claims = await claim_service.extract_claims_for_story(test_db, story)
    assert len(claims) > 0
    assert claims[0].source_article_id == art.id

    # Verify story
    vr = await verification_service.verify_story(test_db, story)
    assert vr.status == "INSUFFICIENT_EVIDENCE"
    assert "Single-source report" in vr.explanation
    # Confidence score heuristic is capped for single sources
    assert vr.confidence_score <= 0.30

@pytest.mark.asyncio
async def test_conflicting_evidence_detected(test_db):
    src1 = NewsSource(name="Publisher A", url="https://a.com/feed")
    src2 = NewsSource(name="Publisher B", url="https://b.com/feed")
    test_db.add_all([src1, src2])
    test_db.commit()

    art1 = Article(
        source_id=src1.id,
        title="Model X scores 92% on MMLU benchmark",
        normalized_title="model x scores 92 on mmlu benchmark",
        canonical_url="https://a.com/model-x-92",
        publisher="Publisher A",
        extracted_text="The creators revealed that Model X scored 92% on the standard MMLU benchmark evaluation.",
        content_hash="h1",
    )
    # Conflicting article reporting a contradictory 81% score
    art2 = Article(
        source_id=src2.id,
        title="Independent testing shows Model X scores 81% on MMLU benchmark",
        normalized_title="independent testing shows model x scores 81 on mmlu benchmark",
        canonical_url="https://b.com/model-x-81",
        publisher="Publisher B",
        extracted_text="Independent evaluators reported that Model X only achieved 81% on MMLU benchmark tests.",
        content_hash="h2",
    )
    test_db.add_all([art1, art2])
    test_db.commit()

    story = Story(
        story_uid="story-conflict",
        headline="Model X MMLU Benchmark Results",
        primary_article_id=art1.id,
        source_count=2,
        independent_source_count=2,
    )
    test_db.add(story)
    test_db.flush()

    sa1 = StoryArticle(story_id=story.id, article_id=art1.id, is_primary=True)
    sa2 = StoryArticle(story_id=story.id, article_id=art2.id, is_primary=False)
    test_db.add_all([sa1, sa2])

    # Add specific checkable claim with 92%
    claim = Claim(
        story_id=story.id,
        source_article_id=art1.id,
        claim_text="Model X achieved a 92% score on the MMLU benchmark.",
        claim_type="metric",
        status="UNVERIFIED",
    )
    test_db.add(claim)
    test_db.commit()

    vr = await verification_service.verify_story(test_db, story)
    assert vr.status == "CONFLICTING"
    assert claim.status == "CONFLICTING"
    assert "Conflicting material evidence" in vr.explanation

@pytest.mark.asyncio
async def test_corroborated_story_with_two_independent_sources(test_db):
    src1 = NewsSource(name="Reuters", url="https://reuters.com/feed")
    src2 = NewsSource(name="Bloomberg", url="https://bloomberg.com/feed")
    test_db.add_all([src1, src2])
    test_db.commit()

    art1 = Article(
        source_id=src1.id,
        title="OpenAI signs multi-year data partnership with Condé Nast",
        normalized_title="openai signs multi-year data partnership with conde nast",
        canonical_url="https://reuters.com/openai-conde-nast",
        publisher="Reuters",
        extracted_text="OpenAI has signed a multi-year content partnership agreement with publisher Condé Nast.",
        content_hash="h1",
    )
    art2 = Article(
        source_id=src2.id,
        title="Condé Nast partners with OpenAI on content integration",
        normalized_title="conde nast partners with openai on content integration",
        canonical_url="https://bloomberg.com/conde-nast-openai",
        publisher="Bloomberg",
        extracted_text="Condé Nast confirmed today it has signed a multi-year content partnership agreement with OpenAI.",
        content_hash="h2",
    )
    test_db.add_all([art1, art2])
    test_db.commit()

    story = Story(
        story_uid="story-corroborated",
        headline="OpenAI and Condé Nast Partnership",
        primary_article_id=art1.id,
        source_count=2,
        independent_source_count=2,
    )
    test_db.add(story)
    test_db.flush()

    sa1 = StoryArticle(story_id=story.id, article_id=art1.id, is_primary=True)
    sa2 = StoryArticle(story_id=story.id, article_id=art2.id, is_primary=False)
    test_db.add_all([sa1, sa2])

    claim = Claim(
        story_id=story.id,
        source_article_id=art1.id,
        claim_text="OpenAI has signed a multi-year content partnership agreement with publisher Condé Nast.",
        claim_type="factual",
        status="UNVERIFIED",
    )
    test_db.add(claim)
    test_db.commit()

    vr = await verification_service.verify_story(test_db, story)
    assert vr.status == "CORROBORATED"
    assert claim.status == "CORROBORATED"
    assert vr.confidence_score >= 0.70
