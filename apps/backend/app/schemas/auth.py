from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request schema for user login."""
    
    email: EmailStr
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
    """Request schema for password reset initiation."""
    
    email: EmailStr


# Import UserBasic for forward reference
from app.schemas.user import UserBasic

LoginResponse.model_rebuild()
