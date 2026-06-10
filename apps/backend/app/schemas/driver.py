from datetime import datetime, date
from uuid import UUID
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, field_validator

from app.models.driver import DriverStatus, LicenseClass


class DriverBase(BaseModel):
    user_id: Optional[UUID] = None
    first_name: str
    last_name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    employee_id: Optional[str] = None
    license_no: str
    license_class: LicenseClass
    license_expiry: date
    base_location: Optional[str] = None  # e.g. "Mumbai Depot"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: Optional[str] = None


class DriverCreate(DriverBase):
    status: DriverStatus = DriverStatus.AVAILABLE
    # IDs of trucks this driver is qualified to operate (many-to-many mapping)
    assigned_truck_ids: Optional[List[UUID]] = []

    @field_validator("license_expiry")
    @classmethod
    def validate_license_expiry(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("License expiry date must be in the future for new drivers")
        return v

    @field_validator("license_no")
    @classmethod
    def validate_license_no(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 7:
            raise ValueError("Phone number must be at least 7 digits")
        return v


class DriverUpdate(BaseModel):
    user_id: Optional[UUID] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    employee_id: Optional[str] = None
    license_no: Optional[str] = None
    license_class: Optional[LicenseClass] = None
    license_expiry: Optional[date] = None
    base_location: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: Optional[str] = None
    # Provide a new list of truck IDs to replace existing qualified-truck assignments
    assigned_truck_ids: Optional[List[UUID]] = None


class DriverAvailabilityUpdate(BaseModel):
    is_available: bool
    status: Optional[DriverStatus] = None


class DriverLocationUpdate(BaseModel):
    """Lightweight payload for updating a driver's real-time GPS position."""
    current_lat: Optional[Decimal] = None
    current_lon: Optional[Decimal] = None
    base_location: Optional[str] = None  # optionally also update home depot


class AssignedTruckBasic(BaseModel):
    id: UUID
    registration_no: str
    truck_type: str

    model_config = {"from_attributes": True}


class DriverResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID] = None
    employee_id: Optional[str] = None
    first_name: str
    last_name: str
    full_name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    license_no: str
    license_class: LicenseClass
    license_expiry: date
    status: DriverStatus
    is_available: bool
    is_license_valid: bool
    is_allocatable: bool
    base_location: Optional[str] = None
    current_lat: Optional[Decimal] = None
    current_lon: Optional[Decimal] = None
    assigned_trucks: List[AssignedTruckBasic] = []
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DriverListResponse(BaseModel):
    items: List[DriverResponse]
    total: int
    page: int
    size: int
    pages: int
