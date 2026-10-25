import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import Story, Claim, Evidence, Article, VerificationResult
from app.services.ollama_service import ollama_service
from app.services.clustering_service import extract_informative_tokens

EVIDENCE_ASSESSMENT_PROMPT = """You are an objective news verification analyst.
Evaluate whether the following article text SUPPORTS, CONTRADICTS, or provides INSUFFICIENT evidence for the target claim.
Target Claim: "{claim_text}"

RULES:
1. Ground your answer ONLY in the text snippet provided.
2. If the text mentions different numbers, dates, or conflicting names, mark verdict as "CONTRADICTS" and explain the discrepancy.
3. If the text confirms the claim, mark verdict as "SUPPORTS" and extract the exact quote snippet.
4. If the text does not mention this claim specifically, mark verdict as "INSUFFICIENT".
5. Output format: Strictly valid JSON:
{
  "verdict": "SUPPORTS | CONTRADICTS | INSUFFICIENT",
  "snippet": "Short direct quotation or relevant sentence from text",
  "material_discrepancy": "Description of any number/date mismatch or null"
}
"""

class VerificationService:
    async def verify_story(self, db: Session, story: Story) -> VerificationResult:
        """
        Executes end-to-end evidence cross-validation across all clustered sources for a story.
        Applies deterministic rules, detects discrepancies, and computes a heuristic confidence score.
        """
        claims = db.query(Claim).filter(Claim.story_id == story.id).all()
        if not claims:
            # Nothing to verify yet
            story.verification_status = "UNVERIFIED"
            story.confidence_score = 0.0
            story.verification_explanation = "No claims extracted yet for verification."
            db.commit()
            res = VerificationResult(
                story_id=story.id,
                status="UNVERIFIED",
                confidence_score=0.0,
                explanation="No claims extracted yet.",
                independent_sources_count=story.independent_source_count,
                total_claims_count=0,
                corroborated_claims_count=0,
                conflicting_claims_count=0,
                unverified_claims_count=0,
            )
            db.add(res)
            db.commit()
            return res

        # Gather all articles linked to this story
        story_articles = [sa.article for sa in story.articles if sa.article]
        
        # Determine independent publisher count
        unique_publishers = {a.publisher.strip().lower() for a in story_articles if a.publisher}
        independent_count = len(unique_publishers)
        story.independent_source_count = independent_count

        total_claims = len(claims)
        corroborated_count = 0
        conflicting_count = 0
        insufficient_count = 0

        # Delete existing evidence for a clean verification pass
        for claim in claims:
            for ev in claim.evidence_items:
                db.delete(ev)
        db.flush()

        for claim in claims:
            claim_tokens = extract_informative_tokens(claim.claim_text)
            claim_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", claim.claim_text))

            supporting_sources = set()
            contradicting_sources = set()

            for article in story_articles:
                is_source_article = (article.id == claim.source_article_id)
                text_to_search = article.extracted_text or article.feed_description or article.title

                # Perform deterministic evidence evaluation
                verdict, snippet, discrepancy = self._evaluate_evidence_deterministic(
                    claim_text=claim.claim_text,
                    claim_tokens=claim_tokens,
                    claim_numbers=claim_numbers,
                    article_text=text_to_search,
                    is_origin=is_source_article
                )

                # If LLM is available and we have a secondary source, we can optionally refine
                if not is_source_article and verdict == "INSUFFICIENT":
                    llm_verdict = await self._evaluate_evidence_with_llm(claim.claim_text, article)
                    if llm_verdict:
                        verdict = llm_verdict["verdict"]
                        snippet = llm_verdict["snippet"] or snippet
                        discrepancy = llm_verdict.get("material_discrepancy")

                # Is independent source?
                origin_article = next((a for a in story_articles if a.id == claim.source_article_id), None)
                is_independent = True
                if origin_article and origin_article.publisher.strip().lower() == article.publisher.strip().lower() and not is_source_article:
                    is_independent = False # Same publisher or syndicated duplicate

                evidence = Evidence(
                    claim_id=claim.id,
                    article_id=article.id,
                    verdict=verdict,
                    snippet=snippet[:500],
                    material_discrepancy=discrepancy,
                    is_independent_source=is_independent,
                    confidence=1.0 if is_source_article else 0.85,
                )
                db.add(evidence)

                if verdict == "SUPPORTS" and not is_source_article and is_independent:
                    supporting_sources.add(article.publisher)
                elif verdict == "CONTRADICTS":
                    contradicting_sources.add(article.publisher)

            # Assign Claim Status based on independent evidence
            if contradicting_sources:
                claim.status = "CONFLICTING"
                claim.verification_notes = f"Conflicting details reported by: {', '.join(contradicting_sources)}."
                conflicting_count += 1
            elif len(supporting_sources) >= 1:
                claim.status = "CORROBORATED"
                claim.verification_notes = f"Corroborated by independent reporting from {', '.join(supporting_sources)}."
                corroborated_count += 1
            else:
                if independent_count <= 1:
                    claim.status = "INSUFFICIENT_EVIDENCE"
                    claim.verification_notes = "Single-source report. No independent cross-sources available for verification."
                else:
                    claim.status = "UNVERIFIED"
                    claim.verification_notes = "Mentioned in primary source, but independent corroboration was not found in other coverage."
                insufficient_count += 1

        db.flush()

        # Story-Level Status Adjudication (Strict deterministic rules)
        # 1. Single-source check
        if independent_count <= 1:
            story_status = "INSUFFICIENT_EVIDENCE"
            explanation = (
                f"Single-source report ({story_articles[0].publisher if story_articles else 'Unknown'}). "
                "No independent cross-publisher reporting is available to corroborate the claims."
            )
            confidence = 0.25
        # 2. Conflicting check
        elif conflicting_count > 0:
            story_status = "CONFLICTING"
            explanation = (
                f"Conflicting material evidence detected across {independent_count} independent sources. "
                f"{conflicting_count} claim(s) contain contradictory dates, numbers, or facts."
            )
            confidence = 0.35
        # 3. All or majority corroborated
        elif corroborated_count == total_claims:
            story_status = "CORROBORATED"
            explanation = (
                f"All {total_claims} claims corroborated across {independent_count} independent sources. "
                "Factual consistency observed without contradictions."
            )
            confidence = min(0.95, 0.60 + (independent_count * 0.12))
        elif corroborated_count > 0:
            story_status = "PARTIALLY_CORROBORATED"
            explanation = (
                f"Partially corroborated: {corroborated_count} of {total_claims} claims verified by independent sources. "
                f"{insufficient_count} claim(s) lack secondary verification."
            )
            confidence = 0.55 + (corroborated_count / total_claims) * 0.25
        else:
            story_status = "UNVERIFIED"
            explanation = (
                f"Story has {independent_count} related articles, but none of the specific checkable claims "
                "could be corroborated independently."
            )
            confidence = 0.20

        # Heuristic confidence calculation
        # Factors: Evidence Coverage (40%), Source Independence (35%), Consistency (25%)
        coverage_ratio = corroborated_count / total_claims if total_claims else 0
        independence_factor = min(1.0, independent_count / 3.0)
        consistency_factor = 0.0 if conflicting_count > 0 else 1.0

        heuristic_confidence = round(
            (coverage_ratio * 0.40) + (independence_factor * 0.35) + (consistency_factor * 0.25),
            2
        )
        # Cap single source stories to max 0.30 confidence
        if independent_count <= 1:
            heuristic_confidence = min(0.30, heuristic_confidence)

        story.verification_status = story_status
        story.confidence_score = heuristic_confidence
        story.verification_explanation = explanation

        # Persist VerificationResult audit record
        vr = VerificationResult(
            story_id=story.id,
            status=story_status,
            confidence_score=heuristic_confidence,
            explanation=explanation,
            independent_sources_count=independent_count,
            total_claims_count=total_claims,
            corroborated_claims_count=corroborated_count,
            conflicting_claims_count=conflicting_count,
            unverified_claims_count=insufficient_count,
        )
        db.add(vr)
        db.commit()
        return vr

    def _evaluate_evidence_deterministic(
        self,
        claim_text: str,
        claim_tokens: set,
        claim_numbers: set,
        article_text: str,
        is_origin: bool
    ) -> tuple[str, str, Optional[str]]:
        """
        Deterministic rule-based evidence evaluator.
        Finds highest matching sentences in the target article and checks for numerical/date conflict.
        """
        if is_origin:
            return "SUPPORTS", claim_text[:300], None

        sentences = re.split(r"(?<=[.!?])\s+", article_text)
        best_sentence = ""
        best_overlap = 0

        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) < 20:
                continue
            s_tokens = extract_informative_tokens(s_clean)
            overlap = len(claim_tokens.intersection(s_tokens))
            if overlap > best_overlap:
                best_overlap = overlap
                best_sentence = s_clean

        # Need at least 2 key overlapping tokens to be relevant
        if best_overlap < 2 or not best_sentence:
            return "INSUFFICIENT", "Article does not contain relevant statements matching this claim.", None

        # Check for numerical / date discrepancies
        sentence_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", best_sentence))
        if claim_numbers and sentence_numbers:
            # If the candidate sentence has numbers in the exact same semantic context but none match
            if not claim_numbers.intersection(sentence_numbers) and best_overlap >= 3:
                return (
                    "CONTRADICTS",
                    best_sentence[:300],
                    f"Numerical discrepancy: claim cites {list(claim_numbers)}, but source states {list(sentence_numbers)}"
                )

        if best_overlap >= 3:
            return "SUPPORTS", best_sentence[:300], None

        return "INSUFFICIENT", best_sentence[:300], None

    async def _evaluate_evidence_with_llm(self, claim_text: str, article: Article) -> Optional[Dict[str, Any]]:
        """Optional LLM assistance for nuanced textual evidence classification."""
        text_snippet = (article.extracted_text or article.feed_description or "")[:2000]
        prompt = (
            f"Evaluate evidence for this claim:\nClaim: \"{claim_text}\"\n\n"
            f"Source Publisher: {article.publisher}\n"
            f"Source Text:\n{text_snippet}"
        )
        res = await ollama_service.generate_json(
            system_prompt=EVIDENCE_ASSESSMENT_PROMPT.replace("{claim_text}", claim_text),
            user_prompt=prompt
        )
        if res and res.get("verdict") in ("SUPPORTS", "CONTRADICTS", "INSUFFICIENT"):
            return {
                "verdict": res["verdict"],
                "snippet": str(res.get("snippet", ""))[:400],
                "material_discrepancy": res.get("material_discrepancy")
            }
        return None

verification_service = VerificationService()
