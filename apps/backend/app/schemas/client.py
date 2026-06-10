from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional, List
import re

from pydantic import BaseModel, field_validator

from app.models.client import ClientType


class ClientBase(BaseModel):
    client_type: ClientType = ClientType.COMPANY
    company_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: str
    alternate_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gst_no: Optional[str] = None
    pan_no: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms_days: Optional[int] = 30
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Company name must be at least 2 characters")
        return v

    @field_validator("gst_no")
    @classmethod
    def validate_gst_no(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip().upper()
            if len(v) != 15:
                raise ValueError("GST number must be exactly 15 characters")
        return v

    @field_validator("credit_limit")
    @classmethod
    def validate_credit_limit(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < 0:
            raise ValueError("Credit limit cannot be negative")
        return v

    @field_validator("payment_terms_days")
    @classmethod
    def validate_payment_terms(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Payment terms days cannot be negative")
        return v

    @field_validator("phone", "alternate_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            if not re.match(r"^\+?91[\s-]?\d{10}$|^\d{10}$", v):
                raise ValueError("Invalid phone format. Supported formats: +91 9789723394 or 9789723394")
        return v


class ClientUpdate(BaseModel):
    client_type: Optional[ClientType] = None
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gst_no: Optional[str] = None
    pan_no: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms_days: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

    @field_validator("phone", "alternate_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            if not re.match(r"^\+?91[\s-]?\d{10}$|^\d{10}$", v):
                raise ValueError("Invalid phone format. Supported formats: +91 9789723394 or 9789723394")
        return v


class ClientResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    client_type: ClientType
    company_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: str
    alternate_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gst_no: Optional[str] = None
    pan_no: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    payment_terms_days: Optional[int] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientListResponse(BaseModel):
    items: List[ClientResponse]
    total: int
    page: int
    size: int
    pages: int
