"""Shared datetime helpers.

`datetime.utcnow()` is deprecated (and scheduled for removal) in favour of
timezone-aware `datetime.now(timezone.utc)`. All DB columns in this project are
naive `DateTime` (UTC by convention), so `utc_now()` returns a naive UTC
datetime — a drop-in, non-deprecated replacement for `datetime.utcnow()`.
"""
from datetime import datetime, timezone

import pytz

from app.config import get_settings


def utc_now() -> datetime:
    """Current UTC time as a naive datetime (matches existing `DateTime` columns)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_for_display(dt: datetime | None, tz_name: str | None = None) -> str | None:
    """Render a naive UTC datetime as a ready-to-display string in the given timezone.

    Falls back to `settings.DEFAULT_TIMEZONE` if `tz_name` is None or invalid.
    Example: "10 Jun 2026, 06:30 PM IST".
    """
    if dt is None:
        return None

    try:
        tz = pytz.timezone(tz_name) if tz_name else pytz.timezone(get_settings().DEFAULT_TIMEZONE)
    except pytz.UnknownTimeZoneError:
        tz = pytz.timezone(get_settings().DEFAULT_TIMEZONE)

    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    return dt.astimezone(tz).strftime("%d %b %Y, %I:%M %p %Z")
