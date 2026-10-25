import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import Article, Claim, Story
from app.services.ollama_service import ollama_service

CLAIM_EXTRACTION_SYSTEM_PROMPT = """You are an objective news intelligence claim extractor.
Your task is to extract 2 to 4 concrete, checkable, factual claims made in the provided article.
RULES:
1. Every claim must be grounded ONLY in the provided article text.
2. Focus on specific material details: dates, numbers, version names, product releases, benchmark scores, or formal statements.
3. Do NOT include opinions, promotional hype, or speculative commentary.
4. Output must be strictly valid JSON matching this format:
{
  "claims": [
    {
      "claim_text": "Exact factual claim",
      "claim_type": "factual | metric | date | technical",
      "material_value": "Optional specific number, version, or date mentioned"
    }
  ]
}
"""

class ClaimService:
    async def extract_claims_for_story(self, db: Session, story: Story) -> List[Claim]:
        """
        Extracts factual claims from the story's primary article (or first available article)
        and associates each claim with the exact source article ID.
        Uses Ollama when available, with a deterministic rule-based fallback.
        """
        # Determine primary article
        primary_sa = next((sa for sa in story.articles if sa.is_primary and sa.article), None)
        if not primary_sa and story.articles:
            primary_sa = story.articles[0]

        if not primary_sa or not primary_sa.article:
            return []

        article = primary_sa.article
        article_text = article.extracted_text or article.feed_description or article.title

        extracted_items: List[Dict[str, Any]] = []

        # Try LLM extraction first
        guarded_input = ollama_service.format_untrusted_article(
            title=article.title,
            publisher=article.publisher,
            text=article_text
        )

        llm_response = await ollama_service.generate_json(
            system_prompt=CLAIM_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=f"Extract verifiable factual claims from this article:\n\n{guarded_input}"
        )

        if llm_response and isinstance(llm_response.get("claims"), list) and len(llm_response["claims"]) > 0:
            for c in llm_response["claims"]:
                if isinstance(c, dict) and c.get("claim_text"):
                    extracted_items.append({
                        "claim_text": c["claim_text"].strip(),
                        "claim_type": c.get("claim_type", "factual"),
                        "material_value": c.get("material_value"),
                    })

        # Deterministic rule-based fallback if LLM is offline or returned empty
        if not extracted_items:
            extracted_items = self._extract_claims_deterministic(article.title, article_text)

        # Remove previous claims for this story if regenerating
        existing_claims = db.query(Claim).filter(Claim.story_id == story.id).all()
        for ec in existing_claims:
            db.delete(ec)
        db.flush()

        created_claims = []
        for item in extracted_items[:5]: # Max 5 claims
            claim = Claim(
                story_id=story.id,
                source_article_id=article.id,
                claim_text=item["claim_text"],
                claim_type=item.get("claim_type", "factual"),
                status="UNVERIFIED",
                verification_notes=f"Extracted from {article.publisher} report.",
            )
            db.add(claim)
            created_claims.append(claim)

        db.commit()
        return created_claims

    def _extract_claims_deterministic(self, title: str, text: str) -> List[Dict[str, Any]]:
        """
        Extracts key sentences containing numbers, versions, dates, or announcement verbs.
        Acts as a reliable offline fallback.
        """
        claims = []
        # First claim from title
        claims.append({
            "claim_text": title.strip(),
            "claim_type": "factual",
            "material_value": None,
        })

        # Split text into candidate sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        metric_regex = re.compile(r"(\b\d+(\.\d+)?%?\b|\bv?\d+\.\d+\b|\b\$?\d+\s*(billion|million)?\b)", re.IGNORECASE)

        for s in sentences:
            s_clean = s.strip()
            if 35 < len(s_clean) < 220 and metric_regex.search(s_clean):
                claims.append({
                    "claim_text": s_clean,
                    "claim_type": "metric",
                    "material_value": None,
                })
                if len(claims) >= 3:
                    break

        return claims

claim_service = ClaimService()
