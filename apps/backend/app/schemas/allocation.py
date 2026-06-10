from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request schemas ───────────────────────────────────────────────────────────

class AllocationCreate(BaseModel):
    """Request to assign truck + driver to a load."""
    truck_id: UUID
    driver_id: UUID
    notes: Optional[str] = Field(None, max_length=500)


class AllocationUpdate(BaseModel):
    """Request to reallocate (swap) truck and/or driver."""
    truck_id: UUID
    driver_id: UUID
    notes: Optional[str] = Field(None, max_length=500)


class DeallocationRequest(BaseModel):
    """Optional reason when deallocating."""
    reason: Optional[str] = Field(None, max_length=500)


# ── Response schemas ──────────────────────────────────────────────────────────

class AllocationResponse(BaseModel):
    id: UUID
    load_id: UUID
    truck_id: UUID
    driver_id: UUID
    pickup_date: date
    effective_delivery_date: date
    is_active: bool
    allocated_by: Optional[UUID] = None
    deactivated_at: Optional[datetime] = None
    deactivated_by: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AvailableTruckItem(BaseModel):
    id: UUID
    registration_no: str
    truck_type: str
    capacity_tons: Optional[Decimal] = None
    make: Optional[str] = None
    model: Optional[str] = None

    model_config = {"from_attributes": True}


class AvailableDriverItem(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    phone: str
    license_no: str
    license_class: str
    license_expiry: date

    model_config = {"from_attributes": True}


class AvailableTrucksResponse(BaseModel):
    items: List[AvailableTruckItem]
    total: int
    pickup_date: date
    effective_delivery_date: date


class AvailableDriversResponse(BaseModel):
    items: List[AvailableDriverItem]
    total: int
    pickup_date: date
    effective_delivery_date: date
