from datetime import date, time
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.load import GoodsType, LoadStatus
from app.schemas.common import LocalDateTime


class LoadBase(BaseModel):
    """Shared editable fields for load create and update."""
    origin: str = Field(..., min_length=2, max_length=255)
    destination: str = Field(..., min_length=2, max_length=255)
    pickup_date: date
    pickup_time: Optional[time] = None
    expected_delivery_date: Optional[date] = None
    goods_type: GoodsType = GoodsType.GENERAL
    goods_description: Optional[str] = Field(None, max_length=500)
    weight_kg: Optional[Decimal] = Field(None, ge=0)
    volume_cbm: Optional[Decimal] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=1)
    distance_km: Optional[Decimal] = Field(None, ge=0)
    freight_amount: Optional[Decimal] = Field(None, ge=0)
    advance_amount: Optional[Decimal] = Field(None, ge=0)
    truck_preference: Optional[str] = Field(None, max_length=100)
    special_instructions: Optional[str] = None
    notes: Optional[str] = None


# ── Create ─────────────────────────────────────────────────────────────────────

class LoadCreate(LoadBase):
    """Schema for creating a new load."""
    client_id: UUID

    @field_validator("origin", "destination")
    @classmethod
    def strip_location(cls, v: str) -> str:
        return v.strip()

    @field_validator("pickup_date")
    @classmethod
    def pickup_not_in_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("pickup_date cannot be in the past")
        return v

    @model_validator(mode="after")
    def delivery_after_pickup(self) -> "LoadCreate":
        if self.expected_delivery_date and self.expected_delivery_date < self.pickup_date:
            raise ValueError("expected_delivery_date must be on or after pickup_date")
        return self

    @model_validator(mode="after")
    def advance_not_exceed_freight(self) -> "LoadCreate":
        if (
            self.freight_amount is not None
            and self.advance_amount is not None
            and self.advance_amount > self.freight_amount
        ):
            raise ValueError("advance_amount cannot exceed freight_amount")
        return self


class PortalLoadCreate(LoadBase):
    """Schema for a Client-portal booking request — `client_id` is resolved
    server-side from the logged-in user's linked Client record (see app/api/v1/portal.py).

    `tenant_id` selects which carrier (of the shipper's linked relationships) this
    booking request is for — a shipper may have relationships with multiple tenants."""

    tenant_id: UUID

    @field_validator("origin", "destination")
    @classmethod
    def strip_location(cls, v: str) -> str:
        return v.strip()

    @field_validator("pickup_date")
    @classmethod
    def pickup_not_in_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("pickup_date cannot be in the past")
        return v

    @model_validator(mode="after")
    def delivery_after_pickup(self) -> "PortalLoadCreate":
        if self.expected_delivery_date and self.expected_delivery_date < self.pickup_date:
            raise ValueError("expected_delivery_date must be on or after pickup_date")
        return self

    @model_validator(mode="after")
    def advance_not_exceed_freight(self) -> "PortalLoadCreate":
        if (
            self.freight_amount is not None
            and self.advance_amount is not None
            and self.advance_amount > self.freight_amount
        ):
            raise ValueError("advance_amount cannot exceed freight_amount")
        return self


# ── Update ─────────────────────────────────────────────────────────────────────

class LoadUpdate(BaseModel):
    """Schema for updating load metadata. client_id and load_no are immutable."""
    origin: Optional[str] = Field(None, min_length=2, max_length=255)
    destination: Optional[str] = Field(None, min_length=2, max_length=255)
    pickup_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    goods_type: Optional[GoodsType] = None
    goods_description: Optional[str] = Field(None, max_length=500)
    weight_kg: Optional[Decimal] = Field(None, ge=0)
    volume_cbm: Optional[Decimal] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=1)
    distance_km: Optional[Decimal] = Field(None, ge=0)
    freight_amount: Optional[Decimal] = Field(None, ge=0)
    advance_amount: Optional[Decimal] = Field(None, ge=0)
    special_instructions: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("pickup_date")
    @classmethod
    def pickup_not_in_past(cls, v: Optional[date]) -> Optional[date]:
        if v and v < date.today():
            raise ValueError("pickup_date cannot be in the past")
        return v


# ── Status transition ─────────────────────────────────────────────────────────

class LoadStatusTransition(BaseModel):
    """Request to transition a load to a new status."""
    to_status: LoadStatus
    remarks: Optional[str] = Field(None, max_length=1000)


class LoadCancelRequest(BaseModel):
    """Request to cancel a load."""
    reason: str = Field(..., min_length=5, max_length=500)


class LoadCheckpointRequest(BaseModel):
    """Request to record a checkpoint (e.g. "Reached Pickup") — appends a
    `LoadHistory` entry without changing `status` (see
    `LoadService.add_checkpoint`)."""
    label: str = Field(..., min_length=2, max_length=100)


# ── Response schemas ──────────────────────────────────────────────────────────

class LoadHistoryResponse(BaseModel):
    id: UUID
    load_id: UUID
    from_status: Optional[LoadStatus] = None
    to_status: LoadStatus
    changed_by: Optional[UUID] = None
    remarks: Optional[str] = None
    changed_at: LocalDateTime

    model_config = {"from_attributes": True}


class LoadResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    load_no: str
    load_seq_no: int
    status: LoadStatus
    client_id: UUID
    client_name: Optional[str] = None

    origin: str
    destination: str
    distance_km: Optional[Decimal] = None

    pickup_date: date
    pickup_time: Optional[time] = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None

    goods_type: GoodsType
    goods_description: Optional[str] = None
    weight_kg: Optional[Decimal] = None
    volume_cbm: Optional[Decimal] = None
    quantity: Optional[int] = None

    freight_amount: Optional[Decimal] = None
    advance_amount: Optional[Decimal] = None
    balance_amount: float          # Computed property from model

    truck_preference: Optional[str] = None
    special_instructions: Optional[str] = None
    notes: Optional[str] = None

    booked_by: Optional[UUID] = None
    cancelled_by: Optional[UUID] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[LocalDateTime] = None

    # Phase 4 Allocation
    allocated_truck_id: Optional[UUID] = None
    allocated_driver_id: Optional[UUID] = None
    allocated_at: Optional[LocalDateTime] = None
    allocated_by: Optional[UUID] = None

    is_editable: bool              # Computed property from model
    is_deletable: bool             # Computed property from model

    created_at: LocalDateTime
    updated_at: LocalDateTime

    model_config = {"from_attributes": True}


class LoadListResponse(BaseModel):
    items: List[LoadResponse]
    total: int
    page: int
    size: int
    pages: int


class PortalLoadResponse(LoadResponse):
    """A LoadResponse plus which carrier (tenant) it belongs to — used when the
    customer portal aggregates shipments across multiple linked carriers."""
    carrier_name: str


class PortalLoadListResponse(BaseModel):
    items: List[PortalLoadResponse]
    total: int
    page: int
    size: int
    pages: int
