from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import UserEmail, validate_password_complexity


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: UserEmail
    password: str = Field(..., min_length=8, max_length=128)


class LoginResponse(BaseModel):
    """Response schema for successful login."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: "UserBasic"
    
    model_config = {"from_attributes": True}


class TokenRefreshRequest(BaseModel):
    """Request schema for token refresh."""
    
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """Response schema for token refresh."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayloadSchema(BaseModel):
    """Schema for JWT token payload."""
    
    sub: UUID = Field(..., description="User ID")
    tenant_id: UUID | None = Field(None, description="Tenant ID")
    role: str | None = Field(None, description="Primary role name")
    exp: datetime
    iat: datetime
    jti: str | None = Field(None, description="JWT ID for revocation")
    type: str = Field("access", description="Token type")


class PasswordChangeRequest(BaseModel):
    """Request schema for password change."""
    
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password must be at least 8 characters"
    )


class PasswordResetRequest(BaseModel):
    """Request schema for password reset initiation (POST /auth/forgot-password)."""

    email: UserEmail


class PasswordResetResponse(BaseModel):
    """Response for POST /auth/forgot-password.

    Always returns the same generic `message` regardless of whether the email
    matches an account (avoids email enumeration). `reset_token` is only
    populated when settings.DEBUG=True — there is no email service yet, so this
    is how the reset link is delivered for now."""

    message: str
    reset_token: str | None = None


class PasswordResetConfirm(BaseModel):
    """Request schema for completing a password reset (POST /auth/reset-password)."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _check_password_complexity(cls, v: str) -> str:
        return validate_password_complexity(v)


# Import UserBasic for forward reference
from app.schemas.user import UserBasic

LoginResponse.model_rebuild()
