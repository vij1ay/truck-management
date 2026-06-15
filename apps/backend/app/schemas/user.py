from uuid import UUID

import pytz
from pydantic import BaseModel, Field, field_validator

from app.config import get_settings
from app.schemas.common import LocalDateTime, UserEmail, validate_password_complexity, validate_preferred_language


def _validate_timezone(v: str | None) -> str | None:
    if v is not None and v not in pytz.all_timezones_set:
        raise ValueError(f"Invalid timezone: {v}")
    return v


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: UserEmail
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, max_length=128)
    tenant_id: UUID | None = None
    role_ids: list[UUID] = Field(default_factory=list)
    timezone: str | None = Field(None, description="IANA tz name, e.g. 'Asia/Kolkata'")
    client_id: UUID | None = Field(None, description="Client record to link this portal login to (role=Client)")

    @field_validator("password")
    @classmethod
    def _check_password_complexity(cls, v: str) -> str:
        return validate_password_complexity(v)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        return _validate_timezone(v)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    is_active: bool | None = None
    timezone: str | None = Field(None, description="IANA tz name, e.g. 'Asia/Kolkata'")
    preferred_language: str | None = Field(None, description="ISO 639-1 code, e.g. 'en', 'hi', 'ta'")
    client_id: UUID | None = Field(None, description="Client record to (re)link this portal login to; pass null to unlink")

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        return _validate_timezone(v)

    @field_validator("preferred_language")
    @classmethod
    def validate_preferred_language(cls, v: str | None) -> str | None:
        return validate_preferred_language(v)


class UserBasic(BaseModel):
    """Basic user info for nested responses."""

    id: UUID
    email: UserEmail
    first_name: str
    last_name: str
    tenant_id: UUID | None = None
    
    model_config = {"from_attributes": True}
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class RoleBasic(BaseModel):
    """Basic role info for user responses."""
    
    id: UUID
    name: str
    
    model_config = {"from_attributes": True}


class UserResponse(UserBase):
    """Full user response schema."""

    id: UUID
    tenant_id: UUID | None = None
    is_active: bool
    is_verified: bool
    timezone: str
    preferred_language: str | None = None
    client_id: UUID | None = None
    last_login_at: LocalDateTime | None = None
    created_at: LocalDateTime
    updated_at: LocalDateTime
    roles: list[RoleBasic] = Field(default_factory=list)
    has_avatar: bool = False

    model_config = {"from_attributes": True}

    @field_validator("timezone", mode="before")
    @classmethod
    def default_timezone(cls, v: str | None) -> str:
        """Always expose an effective timezone (falls back to DEFAULT_TIMEZONE)."""
        return v or get_settings().DEFAULT_TIMEZONE


class UserListResponse(BaseModel):
    """Paginated list of users."""
    
    items: list[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class UserActivateRequest(BaseModel):
    """Request to activate/deactivate a user."""

    is_active: bool


class TimezoneListResponse(BaseModel):
    """List of selectable IANA timezone names (pytz.common_timezones)."""

    timezones: list[str]
