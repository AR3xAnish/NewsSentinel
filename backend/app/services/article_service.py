import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from app.utils.security import validate_url_safe, sanitize_html_text
from app.config import get_settings

settings = get_settings()

class ArticleExtractionService:
    def __init__(self):
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    async def extract_article_content(self, url: str, fallback_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Attempts to safely fetch and extract the main article text and metadata.
        Falls back to RSS description if extraction fails or is blocked.
        """
        is_safe, msg = validate_url_safe(url)
        if not is_safe:
            return {
                "extracted_text": sanitize_html_text(fallback_description or ""),
                "extraction_status": "blocked_ssrf",
                "image_url": None,
                "error": msg,
            }

        try:
            async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)
                
                # Check redirect safety (SSRF protection on redirect)
                if response.history:
                    final_url = str(response.url)
                    safe_redirect, r_msg = validate_url_safe(final_url)
                    if not safe_redirect:
                        return {
                            "extracted_text": sanitize_html_text(fallback_description or ""),
                            "extraction_status": "blocked_redirect_ssrf",
                            "image_url": None,
                            "error": r_msg,
                        }

                if response.status_code != 200:
                    return {
                        "extracted_text": sanitize_html_text(fallback_description or ""),
                        "extraction_status": "rss_fallback",
                        "image_url": None,
                        "error": f"HTTP status {response.status_code}",
                    }

                html = response.text
                soup = BeautifulSoup(html, "html.parser")

                # Remove non-content tags
                for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "form", "svg"]):
                    element.decompose()

                # Extract OpenGraph / Twitter image if available
                image_url = None
                og_image = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
                if og_image and og_image.get("content"):
                    image_url = og_image["content"].strip()

                # Search for primary article container
                article_elem = soup.find("article") or soup.find("main") or soup.find("div", class_=lambda c: c and any(w in c.lower() for w in ["article-body", "post-content", "entry-content", "story-body"]))
                
                if article_elem:
                    paragraphs = article_elem.find_all("p")
                else:
                    paragraphs = soup.find_all("p")

                cleaned_paras = []
                for p in paragraphs:
                    text = p.get_text().strip()
                    # Filter out short disclaimers, cookie notices, or social share text
                    if len(text) > 40:
                        cleaned_paras.append(text)

                extracted_text = "\n\n".join(cleaned_paras)

                if len(extracted_text) < 150 and fallback_description:
                    # Fall back to RSS description if extracted text is too sparse
                    extracted_text = sanitize_html_text(fallback_description)
                    extraction_status = "rss_fallback"
                else:
                    extraction_status = "extracted"

                return {
                    "extracted_text": extracted_text[:8000], # protect database and context limits
                    "extraction_status": extraction_status,
                    "image_url": image_url,
                    "error": None,
                }

        except Exception as e:
            return {
                "extracted_text": sanitize_html_text(fallback_description or ""),
                "extraction_status": "rss_fallback",
                "image_url": None,
                "error": str(e),
            }

article_service = ArticleExtractionService()
