import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Numeric, Integer,
    ForeignKey, Text, Enum as SAEnum, Date, DateTime, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, Base, UUIDMixin, TimestampMixin
import uuid


class LoadStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    ALLOCATED = "allocated"        # Reserved for Phase 4 (truck/driver assignment)
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class GoodsType(str, enum.Enum):
    GENERAL = "general"
    HAZARDOUS = "hazardous"
    PERISHABLE = "perishable"
    FRAGILE = "fragile"
    MACHINERY = "machinery"
    CHEMICALS = "chemicals"
    OTHER = "other"


# Allowed status transitions (state machine)
ALLOWED_TRANSITIONS: dict[LoadStatus, list[LoadStatus]] = {
    LoadStatus.DRAFT:      [LoadStatus.CONFIRMED, LoadStatus.CANCELLED],
    LoadStatus.CONFIRMED:  [LoadStatus.ALLOCATED, LoadStatus.CANCELLED],
    LoadStatus.ALLOCATED:  [LoadStatus.CONFIRMED, LoadStatus.IN_TRANSIT, LoadStatus.CANCELLED],
    LoadStatus.IN_TRANSIT: [LoadStatus.DELIVERED, LoadStatus.CANCELLED],
    LoadStatus.DELIVERED:  [],   # Terminal
    LoadStatus.CANCELLED:  [],   # Terminal
}


class Load(BaseModel):
    """Core load/booking entity with lifecycle management."""

    __tablename__ = "loads"

    __table_args__ = (
        # Unique load number per tenant
        Index("ix_loads_tenant_load_no", "tenant_id", "load_no", unique=True),
        # Fast filter by status within tenant
        Index("ix_loads_tenant_status", "tenant_id", "status"),
        # Fast filter by client within tenant
        Index("ix_loads_tenant_client", "tenant_id", "client_id"),
        # Date range queries
        Index("ix_loads_tenant_pickup_date", "tenant_id", "pickup_date"),
    )

    # Multi-tenant
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Human-readable load identifier (LD-YYYY-NNNNNN)
    load_no = Column(String(20), nullable=False, index=True)
    # Internal sequence counter used for load_no generation
    load_seq_no = Column(Integer, nullable=False)

    # Status
    status = Column(
        SAEnum(LoadStatus, name="loadstatus"),
        nullable=False,
        default=LoadStatus.DRAFT,
        index=True
    )

    # Client reference
    client_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Route
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    distance_km = Column(Numeric(10, 2), nullable=True)

    # Schedule
    pickup_date = Column(Date, nullable=False)
    pickup_time = Column(String(5), nullable=True)  # Format HH:MM
    expected_delivery_date = Column(Date, nullable=True)
    actual_delivery_date = Column(Date, nullable=True)

    # Goods
    goods_type = Column(
        SAEnum(GoodsType, name="goodstype"),
        nullable=False,
        default=GoodsType.GENERAL
    )
    goods_description = Column(String(500), nullable=True)
    weight_kg = Column(Numeric(10, 2), nullable=True)
    volume_cbm = Column(Numeric(10, 2), nullable=True)
    quantity = Column(Integer, nullable=True)

    # Financial
    freight_amount = Column(Numeric(15, 2), nullable=True, default=0)
    advance_amount = Column(Numeric(15, 2), nullable=True, default=0)

    # Operational notes
    truck_preference = Column(String(100), nullable=True)
    special_instructions = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Booking metadata
    booked_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Cancellation info
    cancelled_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    cancellation_reason = Column(Text, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Allocation info (set when status = ALLOCATED)
    allocated_truck_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trucks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    allocated_driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    allocated_at = Column(DateTime, nullable=True)
    allocated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="loads")
    client = relationship("Client", back_populates="loads")
    booked_by_user = relationship("User", foreign_keys=[booked_by])
    cancelled_by_user = relationship("User", foreign_keys=[cancelled_by])
    allocated_truck = relationship("Truck", foreign_keys=[allocated_truck_id])
    allocated_driver = relationship("Driver", foreign_keys=[allocated_driver_id])
    allocated_by_user = relationship("User", foreign_keys=[allocated_by])
    history = relationship(
        "LoadHistory",
        back_populates="load",
        order_by="LoadHistory.changed_at",
        cascade="all, delete-orphan"
    )
    allocations = relationship(
        "LoadAllocation",
        back_populates="load",
        order_by="LoadAllocation.created_at",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Load {self.load_no} [{self.status}]>"

    @property
    def balance_amount(self) -> float:
        """Outstanding balance after advance."""
        freight = float(self.freight_amount or 0)
        advance = float(self.advance_amount or 0)
        return max(freight - advance, 0)

    @property
    def is_editable(self) -> bool:
        """Only DRAFT and CONFIRMED loads can be edited."""
        return self.status in (LoadStatus.DRAFT, LoadStatus.CONFIRMED)

    @property
    def is_deletable(self) -> bool:
        """Only DRAFT and CANCELLED loads can be deleted."""
        return self.status in (LoadStatus.DRAFT, LoadStatus.CANCELLED)

    def can_transition_to(self, new_status: LoadStatus) -> bool:
        """Check if transition to new_status is allowed."""
        return new_status in ALLOWED_TRANSITIONS.get(self.status, [])


class LoadHistory(Base, UUIDMixin, TimestampMixin):
    """Immutable audit trail for each load status transition."""

    __tablename__ = "load_history"

    __table_args__ = (
        Index("ix_load_history_load_id", "load_id"),
        Index("ix_load_history_changed_at", "changed_at"),
    )

    load_id = Column(
        UUID(as_uuid=True),
        ForeignKey("loads.id", ondelete="CASCADE"),
        nullable=False,
    )

    from_status = Column(
        SAEnum(LoadStatus, name="loadstatus"),
        nullable=True   # NULL for initial DRAFT creation entry
    )
    to_status = Column(
        SAEnum(LoadStatus, name="loadstatus"),
        nullable=False
    )

    changed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    remarks = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    load = relationship("Load", back_populates="history")
    changed_by_user = relationship("User", foreign_keys=[changed_by])

    def __repr__(self):
        return f"<LoadHistory {self.from_status}→{self.to_status}>"
