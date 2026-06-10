from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    
    password: str = Field(..., min_length=8, max_length=128)
    tenant_id: UUID | None = None
    role_ids: list[UUID] = Field(default_factory=list)
    
    @field_validator("password")
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


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    is_active: bool | None = None


class UserBasic(BaseModel):
    """Basic user info for nested responses."""
    
    id: UUID
    email: EmailStr
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
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    roles: list[RoleBasic] = Field(default_factory=list)
    
    model_config = {"from_attributes": True}


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
