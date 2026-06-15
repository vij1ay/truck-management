import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, PlainSerializer

from app.core.datetime_utils import format_for_display
from app.core.timezone_context import get_current_timezone

# A datetime field that serializes to a ready-to-display string in the current
# request's user timezone (set by app.dependencies.auth.get_current_user), e.g.
# "10 Jun 2026, 06:30 PM IST". Use for any datetime returned to clients for display;
# keep plain `datetime` for inputs / internal-only fields (e.g. JWT exp/iat).
LocalDateTime = Annotated[
    datetime,
    PlainSerializer(
        lambda dt: format_for_display(dt, get_current_timezone()),
        return_type=str | None,
        when_used="json",
    ),
]


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_user_email(v: str) -> str:
    v = v.strip().lower()
    if not _EMAIL_RE.match(v):
        raise ValueError("Invalid email format")
    return v


# Login/account email addresses (User.email, login, password reset, admin_email,
# portal-account linking). Deliberately a structural `local@domain.tld` check
# rather than pydantic's `EmailStr` (backed by `email-validator`), which rejects
# special-use/reserved TLDs like `.local` — and would lock out internal accounts
# such as the seeded SuperAdmin (SUPERADMIN_EMAIL=admin@system.local). Business
# contact emails (Client.email, Driver.email) are plain `Optional[str]` and
# unaffected.
UserEmail = Annotated[str, AfterValidator(_validate_user_email)]


# Languages selectable as a user's preferred UI language (User.preferred_language).
# ISO 639-1 codes — English, Hindi, Tamil. Used by the mobile driver app's language
# picker; the admin web app currently only ships an 'en' translation.
SUPPORTED_LANGUAGES = ["en", "hi", "ta"]


def validate_preferred_language(v: str | None) -> str | None:
    """Shared validator for User.preferred_language (UserCreate/UserUpdate)."""
    if v is not None and v not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language '{v}'. Allowed: {', '.join(SUPPORTED_LANGUAGES)}")
    return v


def validate_password_complexity(v: str) -> str:
    """Shared password complexity rule: used by UserCreate.password and
    ResetPasswordRequest.new_password."""
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    return v


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    
    page: int = 1
    size: int = 50


class MessageResponse(BaseModel):
    """Generic message response."""
    
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error_code: str
    message: str
    details: dict | None = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = "healthy"
    version: str = "0.1.0"
