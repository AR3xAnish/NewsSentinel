import time
from datetime import datetime, timezone, timedelta
from app.utils.url_utils import normalize_url, normalize_title, generate_content_hash
from app.utils.date_utils import safe_parse_date, is_within_lookback

def test_url_normalization_tracking_params():
    raw = "https://techcrunch.com/2026/10/24/new-ai-model/?utm_source=twitter&utm_medium=social&ref=feed&id=123"
    normalized = normalize_url(raw)
    assert "utm_source" not in normalized
    assert "utm_medium" not in normalized
    assert "ref" not in normalized
    assert normalized == "https://techcrunch.com/2026/10/24/new-ai-model?id=123"

def test_url_normalization_trailing_slash_and_port():
    raw1 = "http://example.com:80/path/to/article/"
    raw2 = "https://example.com:443/path/to/article"
    assert normalize_url(raw1) == "http://example.com/path/to/article"
    assert normalize_url(raw2) == "https://example.com/path/to/article"

def test_normalize_title_strips_publisher():
    t1 = "OpenAI Announces GPT-5 With Advanced Reasoning | TechCrunch"
    t2 = "OpenAI Announces GPT-5 With Advanced Reasoning - The Verge"
    t3 = "OpenAI Announces GPT-5 With Advanced Reasoning - OpenAI"

    norm1 = normalize_title(t1)
    norm2 = normalize_title(t2)
    norm3 = normalize_title(t3)

    assert norm1 == norm2 == norm3
    assert "techcrunch" not in norm1
    assert "the verge" not in norm2

def test_content_hash_consistency():
    title = "anthropic launches claude 3 7"
    snippet = "new hybrid reasoning model launched today"
    hash1 = generate_content_hash(title, snippet)
    hash2 = generate_content_hash(title, snippet)
    assert hash1 == hash2
    assert len(hash1) == 64

def test_safe_parse_date_rfc2822():
    rfc = "Fri, 24 Oct 2026 14:30:00 +0000"
    dt = safe_parse_date(rfc)
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.day == 24
    assert dt.tzinfo == timezone.utc

def test_safe_parse_date_struct_time():
    st = time.struct_time((2026, 10, 24, 12, 0, 0, 4, 297, 0))
    dt = safe_parse_date(st)
    assert dt is not None
    assert dt.year == 2026

def test_safe_parse_date_malformed():
    # Never crash, never fabricate
    assert safe_parse_date("not-a-real-date") is None
    assert safe_parse_date("") is None
    assert safe_parse_date(None) is None

def test_is_within_lookback():
    now = datetime.now(timezone.utc)
    recent = now - timedelta(hours=12)
    old = now - timedelta(hours=72)

    assert is_within_lookback(recent, lookback_hours=48)
    assert not is_within_lookback(old, lookback_hours=48)
    # Unknown date is preserved for review
    assert is_within_lookback(None, lookback_hours=48)
