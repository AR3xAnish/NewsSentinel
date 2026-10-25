import hashlib
import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "fbclid", "gclid", "ref", "ref_src", "source", "feature",
    "mc_cid", "mc_eid", "igshid", "_hsenc", "_hsmi"
}

PUBLISHER_SUFFIX_PATTERNS = [
    r"\s*\|\s*[^|]+$", # General pipe brand separator (e.g. | TechCrunch, | Tech News, | BBC)
    r"\s*-\s*The Verge.*$",
    r"\s*-\s*OpenAI.*$",
    r"\s*-\s*Google AI Blog.*$",
    r"\s*-\s*Reuters.*$",
    r"\s*-\s*Bloomberg.*$",
    r"\s*-\s*VentureBeat.*$",
]

def normalize_url(raw_url: str) -> str:
    """
    Normalizes a URL by lowercasing scheme and host, stripping default ports,
    removing tracking/analytics query parameters, sorting remaining parameters,
    and removing trailing slashes on paths (unless it's just the root slash).
    """
    if not raw_url:
        return ""

    raw_url = raw_url.strip()
    try:
        parsed = urlparse(raw_url)
    except Exception:
        return raw_url

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Remove standard default ports
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    # Normalize path
    path = parsed.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    # Filter out tracking query parameters
    query_items = parse_qsl(parsed.query, keep_blank_values=False)
    filtered_items = [
        (k, v) for k, v in query_items
        if k.lower() not in TRACKING_PARAMS
    ]
    # Sort query parameters for consistent canonical representation
    filtered_items.sort(key=lambda x: x[0])
    query = urlencode(filtered_items)

    # Reconstruct normalized URL (ignore fragment)
    normalized = urlunparse((scheme, netloc, path, "", query, ""))
    return normalized

def normalize_title(title: str) -> str:
    """
    Normalizes article title: strips publisher suffixes, lowercases,
    removes special punctuation, collapses whitespace.
    """
    if not title:
        return ""

    cleaned = title.strip()
    # Strip known publisher brand suffixes
    for pattern in PUBLISHER_SUFFIX_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Lowercase
    cleaned = cleaned.lower()
    # Replace non-alphanumeric (except hyphens and spaces)
    cleaned = re.sub(r"[^\w\s-]", " ", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def generate_content_hash(normalized_title: str, text_snippet: str = "") -> str:
    """Creates a deterministic SHA-256 fingerprint for title + snippet."""
    feed = f"{normalized_title}::{text_snippet[:200]}".encode("utf-8")
    return hashlib.sha256(feed).hexdigest()
