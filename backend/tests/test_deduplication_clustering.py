import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.models import NewsSource, Article, Story, StoryArticle
from app.services.deduplication_service import deduplication_service
from app.services.clustering_service import clustering_service, calculate_token_similarity, extract_informative_tokens
from app.utils.url_utils import normalize_url, normalize_title, generate_content_hash

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

def test_deduplication_by_canonical_url(test_db):
    source = NewsSource(name="TechCrunch", url="https://techcrunch.com/feed")
    test_db.add(source)
    test_db.commit()

    art1 = Article(
        source_id=source.id,
        title="Meta Releases Llama 4",
        normalized_title="meta releases llama 4",
        canonical_url="https://techcrunch.com/2026/meta-releases-llama-4",
        publisher="TechCrunch",
        content_hash="abc12345",
    )
    test_db.add(art1)
    test_db.commit()

    # Query with tracking params
    is_dup, reason = deduplication_service.is_duplicate(
        test_db,
        raw_url="https://techcrunch.com/2026/meta-releases-llama-4/?utm_source=twitter",
        title="Meta Releases Llama 4"
    )
    assert is_dup
    assert "Canonical URL" in reason

def test_deduplication_by_content_hash(test_db):
    source = NewsSource(name="Ars Technica", url="https://arstechnica.com/feed")
    test_db.add(source)
    test_db.commit()

    norm_title = normalize_title("Google DeepMind Introduces AlphaFold 3")
    hash_val = generate_content_hash(norm_title)

    art1 = Article(
        source_id=source.id,
        title="Google DeepMind Introduces AlphaFold 3",
        normalized_title=norm_title,
        canonical_url="https://arstechnica.com/alphafold-3",
        publisher="Ars Technica",
        content_hash=hash_val,
    )
    test_db.add(art1)
    test_db.commit()

    # Different URL, identical title content
    is_dup, reason = deduplication_service.is_duplicate(
        test_db,
        raw_url="https://arstechnica.com/different-slug-copy",
        title="Google DeepMind Introduces AlphaFold 3 | Ars Technica"
    )
    assert is_dup
    assert "Normalized title hash" in reason

def test_token_similarity():
    t1 = extract_informative_tokens("Anthropic announces Claude 3.7 Sonnet with hybrid reasoning")
    t2 = extract_informative_tokens("Claude 3.7 Sonnet launched by Anthropic featuring hybrid reasoning")
    sim = calculate_token_similarity(t1, t2)
    assert sim > 0.40

def test_clustering_groups_related_articles(test_db):
    src1 = NewsSource(name="Official OpenAI", url="https://openai.com/rss", is_official=True)
    src2 = NewsSource(name="The Verge", url="https://theverge.com/rss", is_official=False)
    test_db.add_all([src1, src2])
    test_db.commit()

    # Article 1: Official Announcement
    art1 = Article(
        source_id=src1.id,
        title="Introducing GPT-4.5 Advanced Multimodal Architecture",
        normalized_title=normalize_title("Introducing GPT-4.5 Advanced Multimodal Architecture"),
        canonical_url="https://openai.com/blog/gpt-4-5",
        publisher="Official OpenAI",
        feed_description="Today we announce GPT-4.5 with advanced reasoning capabilities and benchmark gains.",
        content_hash="h1",
    )
    test_db.add(art1)
    test_db.commit()

    # First clustering pass
    new_count = clustering_service.cluster_articles(test_db)
    assert new_count == 1
    story = test_db.query(Story).first()
    assert story is not None
    assert story.primary_article_id == art1.id

    # Article 2: Third-party tech reporting on the same event
    art2 = Article(
        source_id=src2.id,
        title="OpenAI launches GPT-4.5 with advanced multimodal reasoning",
        normalized_title=normalize_title("OpenAI launches GPT-4.5 with advanced multimodal reasoning"),
        canonical_url="https://theverge.com/openai-gpt-4-5-multimodal",
        publisher="The Verge",
        feed_description="OpenAI today announced its new GPT-4.5 model featuring multimodal reasoning.",
        content_hash="h2",
    )
    test_db.add(art2)
    test_db.commit()

    # Second clustering pass
    new_count2 = clustering_service.cluster_articles(test_db)
    # Should cluster into existing story, not create a new one
    assert new_count2 == 0
    assert story.source_count == 2
    assert story.independent_source_count == 2
    # Primary article remains the official announcement
    assert story.primary_article_id == art1.id
