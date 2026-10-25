from sqlalchemy.orm import Session
from app.models.models import Article
from app.utils.url_utils import normalize_url, normalize_title, generate_content_hash

class DeduplicationService:
    def is_duplicate(self, db: Session, raw_url: str, title: str) -> tuple[bool, str]:
        """
        Determines whether an incoming article is a duplicate based on:
        1. Canonical normalized URL
        2. Content hash (normalized title + snippet)
        """
        canonical_url = normalize_url(raw_url)
        normalized_title = normalize_title(title)
        content_hash = generate_content_hash(normalized_title)

        # 1. Check exact canonical URL
        existing_by_url = db.query(Article.id).filter(Article.canonical_url == canonical_url).first()
        if existing_by_url:
            return True, f"Canonical URL already exists (Article ID {existing_by_url[0]})"

        # 2. Check title content hash
        existing_by_hash = db.query(Article.id).filter(Article.content_hash == content_hash).first()
        if existing_by_hash:
            return True, f"Normalized title hash already exists (Article ID {existing_by_hash[0]})"

        return False, "Unique"

deduplication_service = DeduplicationService()
