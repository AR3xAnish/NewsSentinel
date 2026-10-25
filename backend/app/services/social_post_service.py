from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import Story, SocialPost, Article
from app.services.ollama_service import ollama_service

SOCIAL_GENERATION_PROMPT = """You are a professional social media intelligence copywriter.
Generate 3 platform-tailored social media drafts based STRICTLY on the verified news evidence provided.
DO NOT use sensationalism, clickbait, or unverified claims.

PLATFORM SPECIFICATIONS:
1. LinkedIn:
   - Professional, editorial, thought-leadership tone
   - Strong hook, explanation of industry impact
   - Include primary source URL: {primary_url}
   - 3-5 relevant hashtags (e.g. #AI #TechNews #Innovation)

2. X (Twitter):
   - CRITICAL: MUST BE UNDER 270 CHARACTERS TOTAL INCLUDING URL AND HASHTAGS.
   - Punchy, factual takeaway.
   - Include URL: {primary_url}
   - Max 2 hashtags.

3. Instagram:
   - Engaging, clear, accessible caption.
   - Break into 2-3 readable short paragraphs with bullet points for key facts.
   - Include source attribution.
   - 5-8 relevant hashtags.

Output must be strictly valid JSON:
{
  "linkedin": "Full LinkedIn draft text...",
  "x": "Full X draft text under 270 chars...",
  "instagram": "Full Instagram caption text...",
  "hashtags": "#AI #Technology #Research"
}
"""

class SocialPostService:
    async def generate_drafts_for_story(
        self,
        db: Session,
        story: Story,
        platforms: Optional[List[str]] = None
    ) -> List[SocialPost]:
        """
        Generates or regenerates platform drafts for a story.
        Saves drafts into the database with character counts and DRAFT status.
        """
        if platforms is None:
            platforms = ["linkedin", "x", "instagram"]

        story_articles = [sa.article for sa in story.articles if sa.article]
        primary_article = next((a for a in story_articles if a.id == story.primary_article_id), None)
        if not primary_article and story_articles:
            primary_article = story_articles[0]

        primary_url = primary_article.canonical_url if primary_article else "https://ygf-ngo.org"
        publisher = primary_article.publisher if primary_article else "Source"

        now = datetime.now(timezone.utc)

        # Context summary
        summary = story.summary_factual or story.headline
        why = story.why_it_matters or "Key developments in AI."

        user_prompt = (
            f"Headline: {story.headline}\n"
            f"Verification Status: {story.verification_status} (Confidence: {story.confidence_score * 100:.0f}%)\n"
            f"Factual Summary: {summary}\n"
            f"Impact: {why}\n"
            f"Publisher: {publisher}\n"
            f"Primary URL: {primary_url}"
        )

        llm_result = await ollama_service.generate_json(
            system_prompt=SOCIAL_GENERATION_PROMPT.replace("{primary_url}", primary_url),
            user_prompt=user_prompt
        )

        posts_data = {}
        if llm_result and isinstance(llm_result, dict):
            posts_data["linkedin"] = llm_result.get("linkedin")
            posts_data["x"] = llm_result.get("x")
            posts_data["instagram"] = llm_result.get("instagram")
            posts_data["hashtags"] = llm_result.get("hashtags", "#AI #Technology")

        # Fallback templates if LLM is offline or field missing
        if not posts_data.get("linkedin"):
            posts_data["linkedin"] = (
                f"📰 Intelligence Brief: {story.headline}\n\n"
                f"{summary}\n\n"
                f"💡 Why it matters: {why}\n\n"
                f"Status: {story.verification_status} ({story.source_count} source(s))\n"
                f"Source: {primary_url}\n\n"
                "#AI #ArtificialIntelligence #Technology #Innovation"
            )

        if not posts_data.get("x"):
            # Enforce strict 280 character limit
            x_headline = story.headline[:120]
            posts_data["x"] = f"📰 {x_headline}\n\nSource: {primary_url}\n#AI #Tech"[:270]

        if not posts_data.get("instagram"):
            posts_data["instagram"] = (
                f"🤖 AI Intelligence Update: {story.headline}\n\n"
                f"{summary}\n\n"
                f"📌 What you should know:\n"
                f"• Verified Status: {story.verification_status}\n"
                f"• Reporting: {publisher}\n\n"
                f"🔗 Link in bio / Read more: {primary_url}\n\n"
                "#ai #tech #innovation #machinelearning #futureoftech"
            )

        saved_posts = []
        for plat in platforms:
            plat_clean = plat.lower().strip()
            content = posts_data.get(plat_clean, "")
            
            # Additional safety clamp for X
            if plat_clean == "x" and len(content) > 280:
                content = content[:275] + "..."

            # Check if post for this platform already exists on this story
            existing_post = db.query(SocialPost).filter(
                SocialPost.story_id == story.id,
                SocialPost.platform == plat_clean
            ).first()

            if existing_post:
                existing_post.content = content
                existing_post.character_count = len(content)
                existing_post.hashtags = posts_data.get("hashtags")
                existing_post.last_regenerated_at = now
                existing_post.updated_at = now
                saved_posts.append(existing_post)
            else:
                new_post = SocialPost(
                    story_id=story.id,
                    platform=plat_clean,
                    content=content,
                    hashtags=posts_data.get("hashtags"),
                    character_count=len(content),
                    status="DRAFT",
                    last_regenerated_at=now,
                    created_at=now,
                    updated_at=now
                )
                db.add(new_post)
                saved_posts.append(new_post)

        db.commit()
        return saved_posts

social_post_service = SocialPostService()
