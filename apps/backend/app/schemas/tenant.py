from uuid import UUID

from pydantic import BaseModel, Field, field_validator
import re

from app.models.tenant import SubscriptionTier
from app.schemas.common import LocalDateTime, UserEmail


class TenantBase(BaseModel):
    """Base tenant schema."""

    name: str = Field(..., min_length=2, max_length=255)
    domain: str | None = Field(None, max_length=255)
    subscription_tier: SubscriptionTier = SubscriptionTier.trial
    max_users: int = Field(default=10, ge=1)


class TenantCreate(TenantBase):
    """Schema for creating a new tenant with admin user."""

    admin_email: UserEmail
    admin_password: str = Field(..., min_length=8, max_length=128)
    admin_first_name: str = Field(..., min_length=1, max_length=100)
    admin_last_name: str = Field(..., min_length=1, max_length=100)
    
    @field_validator("admin_password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    
    name: str | None = Field(None, min_length=2, max_length=255)
    domain: str | None = Field(None, max_length=255)
    subscription_tier: SubscriptionTier | None = None
    max_users: int | None = Field(None, ge=1)
    is_active: bool | None = None
    settings: dict | None = None


class TenantResponse(TenantBase):
    """Full tenant response schema."""
    
    id: UUID
    is_active: bool
    settings: dict = Field(default_factory=dict)
    has_avatar: bool = False
    created_at: LocalDateTime
    updated_at: LocalDateTime
    user_count: int | None = None

    model_config = {"from_attributes": True}


class TenantListResponse(BaseModel):
    """Paginated list of tenants."""
    
    items: list[TenantResponse]
    total: int
    page: int
    size: int
    pages: int
