"""Request-scoped timezone context.

`get_current_user` (app/dependencies/auth.py) sets this to the authenticated
user's `timezone` for the lifetime of the request. Response schemas read it
(via `LocalDateTime`, see app/schemas/common.py) to render datetimes in the
user's local time. Falls back to `settings.DEFAULT_TIMEZONE` for
unauthenticated requests or users without a `timezone` set.
"""
from contextvars import ContextVar

from app.config import get_settings

_current_timezone: ContextVar[str | None] = ContextVar("current_timezone", default=None)


def set_current_timezone(tz: str | None) -> None:
    """Set the timezone for the current request context."""
    _current_timezone.set(tz)


def get_current_timezone() -> str:
    """Get the timezone for the current request context, or the configured default."""
    return _current_timezone.get() or get_settings().DEFAULT_TIMEZONE
