import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import Story, Article
from app.services.ollama_service import ollama_service

SUMMARY_SYSTEM_PROMPT = """You are a rigorous, objective news intelligence editor.
Generate an accurate, factual summary grounded STRICTLY in the provided verified news evidence.
RULES:
1. Do NOT extrapolate or introduce external facts, unverified statistics, or quotes absent from the source texts.
2. Clearly distinguish between what an organization claims vs what independent sources reported.
3. Highlight what remains uncertain or unverified.
4. Output must be strictly valid JSON matching this schema:
{
  "headline": "Concise, objective headline",
  "summary_factual": "1-2 sentence core factual summary",
  "what_happened": "Detailed factual account of the reported event",
  "why_it_matters": "Strategic significance or technical impact for AI/tech ecosystem",
  "key_facts_dates": [
    {"fact": "Concrete fact or metric", "source": "Publisher name"}
  ],
  "what_remains_uncertain": "Known gaps, pending confirmations, or single-source limitations"
}
"""

class SummarizationService:
    async def generate_grounded_summary(self, db: Session, story: Story) -> Story:
        """
        Generates a structured, evidence-grounded summary for a story using Ollama,
        with deterministic fallback when Ollama is unreachable.
        """
        story_articles: List[Article] = [sa.article for sa in story.articles if sa.article]
        if not story_articles:
            return story

        primary_article = next((a for a in story_articles if a.id == story.primary_article_id), story_articles[0])

        # Prepare evidence context
        evidence_snippets = []
        for a in story_articles:
            text = (a.extracted_text or a.feed_description or a.title)[:1200]
            evidence_snippets.append(f"Source [{a.publisher}] (Published: {a.published_at or 'Unknown date'}):\n{text}\n")

        evidence_corpus = "\n---\n".join(evidence_snippets)
        user_prompt = (
            f"Story Title: {story.headline}\n"
            f"Verification Status: {story.verification_status} (Confidence: {story.confidence_score * 100:.0f}%)\n"
            f"Verification Notes: {story.verification_explanation}\n\n"
            f"Verified Evidence Corpus:\n{evidence_corpus}"
        )

        llm_result = await ollama_service.generate_json(
            system_prompt=SUMMARY_SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        now = datetime.now(timezone.utc)

        if llm_result and isinstance(llm_result, dict) and llm_result.get("summary_factual"):
            story.headline = llm_result.get("headline", story.headline)
            story.summary_factual = llm_result.get("summary_factual")
            story.what_happened = llm_result.get("what_happened")
            story.why_it_matters = llm_result.get("why_it_matters")
            facts_list = llm_result.get("key_facts_dates", [])
            story.key_facts_dates = json.dumps(facts_list) if isinstance(facts_list, list) else json.dumps([])
            story.what_remains_uncertain = llm_result.get("what_remains_uncertain")
            story.ai_processed_at = now
        else:
            # Deterministic fallback summary based on primary article and verification state
            primary_text = primary_article.extracted_text or primary_article.feed_description or primary_article.title
            first_para = primary_text.split("\n\n")[0] if "\n\n" in primary_text else primary_text[:350]

            facts = [
                {"fact": f"Reported by {primary_article.publisher}", "source": primary_article.publisher},
            ]
            if primary_article.published_at:
                facts.append({"fact": f"Publication date: {primary_article.published_at.strftime('%Y-%m-%d')}", "source": primary_article.publisher})

            story.summary_factual = first_para[:300]
            story.what_happened = (
                f"{primary_article.publisher} published a report titled '{primary_article.title}'. "
                f"{first_para[:400]}"
            )
            story.why_it_matters = (
                f"Impacts developments in {primary_article.topic or 'artificial intelligence'}. "
                f"Currently supported by {story.independent_source_count} independent source(s)."
            )
            story.key_facts_dates = json.dumps(facts)
            
            if story.independent_source_count <= 1:
                uncertain = f"Single-source report from {primary_article.publisher}. Awaiting independent confirmation or secondary coverage."
            elif story.verification_status == "CONFLICTING":
                uncertain = "Sources disagree on specific factual or numerical details; see Claim analysis."
            else:
                uncertain = "General market adoption, implementation timelines, and long-term verification remain subject to ongoing monitoring."

            story.what_remains_uncertain = uncertain
            story.ai_processed_at = now

        db.commit()
        return story

summarization_service = SummarizationService()
