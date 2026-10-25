import re
import hashlib
from typing import List, Set, Optional
from sqlalchemy.orm import Session
from app.models.models import Article, Story, StoryArticle

STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "is", "are", "was", "were", "be", "been", "has", "have", "had",
    "it", "its", "that", "this", "these", "those", "as", "new", "ai", "artificial",
    "intelligence", "tech", "technology", "news", "announces", "announced", "launch",
    "launches", "launched", "release", "releases", "released", "update", "updates"
}

def extract_informative_tokens(text: str) -> Set[str]:
    """Tokenizes text into meaningful content words and model versions for clustering."""
    if not text:
        return set()
    # Normalize punctuation but retain dots between digits (e.g. 4.5) and hyphens (gpt-4)
    cleaned = re.sub(r"(?<=\D)\.|\.(?=\D)|[^\w\s.-]", " ", text.lower())
    words = cleaned.split()
    return {
        w.strip(".-") for w in words
        if (len(w) >= 2 or any(c.isdigit() for c in w)) and w not in STOPWORDS
    }

def calculate_token_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Calculates Jaccard similarity between two token sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / len(union) if union else 0.0

class ClusteringService:
    def cluster_articles(self, db: Session, lookback_stories_limit: int = 50) -> int:
        """
        Groups unclustered articles into existing or new Stories.
        Preserves individual source records and selects the primary announcement.
        Returns the number of new stories created.
        """
        # Find articles not yet associated with any story
        unclustered_articles = (
            db.query(Article)
            .outerjoin(StoryArticle, Article.id == StoryArticle.article_id)
            .filter(StoryArticle.id.is_(None))
            .order_by(Article.published_at.desc().nullslast(), Article.ingested_at.desc())
            .all()
        )

        if not unclustered_articles:
            return 0

        # Load recent active stories for clustering comparison
        recent_stories = (
            db.query(Story)
            .order_by(Story.created_at.desc())
            .limit(lookback_stories_limit)
            .all()
        )

        new_stories_count = 0

        for article in unclustered_articles:
            article_tokens = extract_informative_tokens(f"{article.title} {article.feed_description or ''}")
            
            matched_story: Optional[Story] = None
            best_similarity = 0.0

            for story in recent_stories:
                story_tokens = extract_informative_tokens(story.headline)
                cluster_tokens = set(story_tokens)
                for sa in story.articles:
                    if sa.article:
                        cluster_tokens.update(extract_informative_tokens(sa.article.title))

                sim = calculate_token_similarity(article_tokens, cluster_tokens)
                common_tokens = article_tokens.intersection(cluster_tokens)

                if sim >= 0.28 and len(common_tokens) >= 2 and sim > best_similarity:
                    best_similarity = sim
                    matched_story = story

            if matched_story:
                # Add to existing story
                is_official = article.source.is_official if article.source else False
                
                # Check if this article should take over as primary
                current_primary = db.query(Article).filter(Article.id == matched_story.primary_article_id).first()
                should_be_primary = False
                if is_official and (not current_primary or not (current_primary.source and current_primary.source.is_official)):
                    should_be_primary = True

                association = StoryArticle(
                    story_id=matched_story.id,
                    article_id=article.id,
                    is_primary=should_be_primary,
                    relevance_score=round(best_similarity, 3)
                )
                db.add(association)

                if should_be_primary:
                    matched_story.primary_article_id = article.id
                    # Demote previous primary in associations
                    for sa in matched_story.articles:
                        if sa.article_id != article.id:
                            sa.is_primary = False

                # Update story source counters
                matched_story.source_count = len(matched_story.articles) + 1
                # Calculate unique publishers
                publishers = {sa.article.publisher for sa in matched_story.articles if sa.article}
                publishers.add(article.publisher)
                matched_story.independent_source_count = len(publishers)

                db.flush()
            else:
                # Create a new story
                story_uid = f"story-{hashlib.sha256(article.canonical_url.encode()).hexdigest()[:16]}"
                new_story = Story(
                    story_uid=story_uid,
                    headline=article.title,
                    primary_article_id=article.id,
                    verification_status="UNVERIFIED",
                    confidence_score=0.2,
                    source_count=1,
                    independent_source_count=1,
                    verification_explanation="Initial single source report. Awaiting corroborating evidence or verification analysis.",
                )
                db.add(new_story)
                db.flush()

                association = StoryArticle(
                    story_id=new_story.id,
                    article_id=article.id,
                    is_primary=True,
                    relevance_score=1.0
                )
                db.add(association)
                db.flush()

                recent_stories.append(new_story)
                new_stories_count += 1

        db.commit()
        return new_stories_count

clustering_service = ClusteringService()
