import enum
from sqlalchemy import Column, String, Boolean, Numeric, Integer, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class TruckType(str, enum.Enum):
    FLATBED = "flatbed"
    CONTAINER = "container"
    TANKER = "tanker"
    REFRIGERATED = "refrigerated"
    TIPPER = "tipper"
    LOWBED = "lowbed"
    OTHER = "other"


class TruckStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    IN_MAINTENANCE = "in_maintenance"
    DECOMMISSIONED = "decommissioned"


class OwnershipType(str, enum.Enum):
    OWNED = "owned"
    CONTRACT = "contract"
    LEASED = "leased"


class Truck(BaseModel):
    """Truck model with full lifecycle management."""

    __tablename__ = "trucks"

    # Multi-tenant
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Identification
    registration_no = Column(String(20), nullable=False, index=True)
    ownership_type = Column(SAEnum(OwnershipType, name="ownershiptype", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    truck_type = Column(SAEnum(TruckType, name="trucktype", values_callable=lambda obj: [e.value for e in obj]), nullable=False)

    # Status
    status = Column(
        SAEnum(TruckStatus, name="truckstatus", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=TruckStatus.ACTIVE
    )
    is_available = Column(Boolean, default=True, nullable=False, index=True)

    # Specs
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    color = Column(String(50), nullable=True)
    capacity_tons = Column(Numeric(10, 2), nullable=True)

    # Driver assignment (optional default driver, actual assignment done in Phase 4)
    assigned_driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # ── OWNED: original owner info ────────────────────────────────
    owner_name    = Column(String(200), nullable=True)  # full name / company
    owner_contact = Column(String(100), nullable=True)  # phone or email

    # ── CONTRACT: third-party fleet operator ──────────────────────
    contractor_name     = Column(String(200), nullable=True)
    contractor_contact  = Column(String(100), nullable=True)
    contract_start_date = Column(String(10),  nullable=True)  # ISO YYYY-MM-DD
    contract_end_date   = Column(String(10),  nullable=True)

    # ── LEASED: leasing company info ─────────────────────────────
    lessor_name       = Column(String(200), nullable=True)
    lessor_contact    = Column(String(100), nullable=True)
    lease_start_date  = Column(String(10),  nullable=True)
    lease_end_date    = Column(String(10),  nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="trucks")
    assigned_driver = relationship("Driver", back_populates="trucks", foreign_keys=[assigned_driver_id])

    # Many-to-many: drivers qualified to operate this truck
    qualified_drivers = relationship("Driver", secondary="driver_trucks", back_populates="assigned_trucks")

    documents = relationship(
        "Document",
        primaryjoin="and_(Document.entity_id == foreign(Truck.id), Document.entity_type == 'truck')",
        viewonly=True,
        lazy="select"
    )
    allocations = relationship("LoadAllocation", back_populates="truck")

    def __repr__(self):
        return f"<Truck {self.registration_no}>"

    @property
    def is_operational(self) -> bool:
        """Check if truck can be allocated to a load."""
        return self.status == TruckStatus.ACTIVE and self.is_available and not self.is_deleted
