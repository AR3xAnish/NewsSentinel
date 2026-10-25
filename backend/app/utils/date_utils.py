from datetime import datetime, timezone, timedelta
import time
from typing import Optional
from email.utils import parsedate_to_datetime

def safe_parse_date(date_raw) -> Optional[datetime]:
    """
    Safely parses diverse date inputs from RSS feeds, time tuples, or ISO strings.
    Never fabricates a timestamp if missing.
    Returns timezone-aware UTC datetime or None.
    """
    if not date_raw:
        return None

    # Handle feedparser time.struct_time tuple
    if isinstance(date_raw, time.struct_time):
        try:
            return datetime.fromtimestamp(time.mktime(date_raw), tz=timezone.utc)
        except Exception:
            return None

    if isinstance(date_raw, datetime):
        if date_raw.tzinfo is None:
            return date_raw.replace(tzinfo=timezone.utc)
        return date_raw.astimezone(timezone.utc)

    if not isinstance(date_raw, str):
        return None

    date_str = date_raw.strip()
    if not date_str:
        return None

    # Try RFC 2822 / email format (common in RSS)
    try:
        dt = parsedate_to_datetime(date_str)
        if dt:
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # Try standard ISO formats
    iso_formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in iso_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue

    return None

def is_within_lookback(published_at: Optional[datetime], lookback_hours: int = 48) -> bool:
    """
    Checks if an article's published_at date falls within the lookback window.
    If published_at is unknown/None, we permit it so it is not dropped blindly,
    distinguishing it from articles clearly older than the window.
    """
    if published_at is None:
        return True # Retain articles with unknown dates for human/ingestion review
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    return published_at >= cutoff
