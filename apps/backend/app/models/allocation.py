from datetime import datetime
from sqlalchemy import (
    Column, Boolean, ForeignKey, Text, DateTime, Date, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.datetime_utils import utc_now
from app.models.base import Base, UUIDMixin, TimestampMixin


class LoadAllocation(Base, UUIDMixin, TimestampMixin):
    """
    Records truck + driver assignment for a load.

    - One load has at most ONE active allocation (is_active=True).
    - Old allocations are preserved with is_active=False when
      a load is reallocated or deallocated (full audit trail).
    - pickup_date / effective_delivery_date are denormalized from the
      parent load to make overlap range-queries fast without joins.
    """

    __tablename__ = "load_allocations"

    __table_args__ = (
        # Overlap detection for trucks
        Index(
            "ix_alloc_truck_dates",
            "truck_id", "is_active", "pickup_date", "effective_delivery_date"
        ),
        # Overlap detection for drivers
        Index(
            "ix_alloc_driver_dates",
            "driver_id", "is_active", "pickup_date", "effective_delivery_date"
        ),
        # Fetch current allocation for a load
        Index("ix_alloc_load_active", "load_id", "is_active"),
    )

    # References
    load_id = Column(
        UUID(as_uuid=True),
        ForeignKey("loads.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    truck_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trucks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    driver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Denormalized date range for conflict queries
    pickup_date = Column(Date, nullable=False)
    effective_delivery_date = Column(Date, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Who allocated
    allocated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Optional notes (e.g. "Emergency swap due to breakdown")
    notes = Column(Text, nullable=True)

    # When was this allocation deactivated (reallocation / deallocation)
    deactivated_at = Column(DateTime, nullable=True)
    deactivated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    load = relationship("Load", back_populates="allocations")
    truck = relationship("Truck", back_populates="allocations")
    driver = relationship("Driver", back_populates="allocations")
    allocated_by_user = relationship("User", foreign_keys=[allocated_by])
    deactivated_by_user = relationship("User", foreign_keys=[deactivated_by])

    def __repr__(self):
        return (
            f"<LoadAllocation load={self.load_id} "
            f"truck={self.truck_id} driver={self.driver_id} "
            f"active={self.is_active}>"
        )

    def deactivate(self, deactivated_by_id, at: datetime | None = None) -> None:
        """Mark this allocation as inactive."""
        self.is_active = False
        self.deactivated_at = at or utc_now()
        self.deactivated_by = deactivated_by_id
