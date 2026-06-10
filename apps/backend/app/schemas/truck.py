from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional, List

from pydantic import BaseModel, field_validator, model_validator

from app.models.truck import TruckType, TruckStatus, OwnershipType


class TruckBase(BaseModel):
    registration_no: str
    ownership_type: OwnershipType
    truck_type: TruckType
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    capacity_tons: Optional[Decimal] = None

    # Owned-truck fields
    owner_name:    Optional[str] = None
    owner_contact: Optional[str] = None   # phone or email

    # Contract-truck fields
    contractor_name:     Optional[str] = None
    contractor_contact:  Optional[str] = None
    contract_start_date: Optional[str] = None   # YYYY-MM-DD
    contract_end_date:   Optional[str] = None

    # Leased-truck fields
    lessor_name:      Optional[str] = None
    lessor_contact:   Optional[str] = None
    lease_start_date: Optional[str] = None
    lease_end_date:   Optional[str] = None

    notes: Optional[str] = None


class TruckCreate(TruckBase):
    assigned_driver_id: Optional[UUID] = None
    status: TruckStatus = TruckStatus.ACTIVE

    @field_validator("registration_no")
    @classmethod
    def validate_registration_no(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) < 3:
            raise ValueError("Registration number must be at least 3 characters")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1980 or v > datetime.now().year + 1):
            raise ValueError(f"Year must be between 1980 and {datetime.now().year + 1}")
        return v

    @field_validator("capacity_tons")
    @classmethod
    def validate_capacity(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v <= 0:
            raise ValueError("Capacity must be greater than 0")
        return v


class TruckUpdate(BaseModel):
    ownership_type: Optional[OwnershipType] = None
    truck_type: Optional[TruckType] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    capacity_tons: Optional[Decimal] = None
    assigned_driver_id: Optional[UUID] = None
    is_available: Optional[bool] = None

    # Owned
    owner_name:    Optional[str] = None
    owner_contact: Optional[str] = None

    # Contract
    contractor_name:     Optional[str] = None
    contractor_contact:  Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date:   Optional[str] = None

    # Leased
    lessor_name:      Optional[str] = None
    lessor_contact:   Optional[str] = None
    lease_start_date: Optional[str] = None
    lease_end_date:   Optional[str] = None

    notes: Optional[str] = None

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1980 or v > datetime.now().year + 1):
            raise ValueError(f"Year must be between 1980 and {datetime.now().year + 1}")
        return v


class TruckResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    registration_no: str
    ownership_type: OwnershipType
    truck_type: TruckType
    status: TruckStatus
    is_available: bool
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    capacity_tons: Optional[Decimal] = None
    assigned_driver_id: Optional[UUID] = None

    # Owned
    owner_name:    Optional[str] = None
    owner_contact: Optional[str] = None

    # Contract
    contractor_name:     Optional[str] = None
    contractor_contact:  Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date:   Optional[str] = None

    # Leased
    lessor_name:      Optional[str] = None
    lessor_contact:   Optional[str] = None
    lease_start_date: Optional[str] = None
    lease_end_date:   Optional[str] = None

    notes: Optional[str] = None
    is_operational: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TruckListResponse(BaseModel):
    items: List[TruckResponse]
    total: int
    page: int
    size: int
    pages: int
