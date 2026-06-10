import enum
from datetime import date
from sqlalchemy import Column, String, Boolean, Date, ForeignKey, Text, Enum as SAEnum, Numeric, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, Base


class DriverStatus(str, enum.Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    ON_LEAVE = "on_leave"
    INACTIVE = "inactive"
    BLACKLISTED = "blacklisted"


class LicenseClass(str, enum.Enum):
    LMV = "lmv"       # Light Motor Vehicle
    HMV = "hmv"       # Heavy Motor Vehicle
    HGV = "hgv"       # Heavy Goods Vehicle
    OTHER = "other"


# Many-to-many association table: a driver can operate multiple trucks,
# and a truck can have multiple qualified drivers.
driver_trucks = Table(
    "driver_trucks",
    Base.metadata,
    Column("driver_id", UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), primary_key=True),
    Column("truck_id",  UUID(as_uuid=True), ForeignKey("trucks.id",  ondelete="CASCADE"), primary_key=True),
)


class Driver(BaseModel):
    """Driver model with license, availability tracking, base location, and GPS support."""

    __tablename__ = "drivers"

    # Multi-tenant
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Identity
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True
    )
    employee_id = Column(String(50), nullable=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)

    # License
    license_no = Column(String(50), nullable=False, index=True)
    license_class = Column(SAEnum(LicenseClass, name="licenseclass", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    license_expiry = Column(Date, nullable=False)

    # Status
    status = Column(
        SAEnum(DriverStatus, name="driverstatus", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=DriverStatus.AVAILABLE
    )
    is_available = Column(Boolean, default=True, nullable=False, index=True)

    # Location — base depot and real-time GPS (to be updated via mobile device)
    base_location = Column(String(255), nullable=True)   # e.g. "Mumbai Depot", "Warehouse B"
    current_lat   = Column(Numeric(10, 7), nullable=True)  # GPS latitude  (future real-time tracking)
    current_lon   = Column(Numeric(10, 7), nullable=True)  # GPS longitude (future real-time tracking)

    # Emergency contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    notes = Column(Text, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="drivers")
    user = relationship("User")

    # One-to-many: trucks that list this driver as their assigned default driver
    trucks = relationship("Truck", back_populates="assigned_driver", foreign_keys="Truck.assigned_driver_id")

    # Many-to-many: trucks this driver is qualified / mapped to operate
    assigned_trucks = relationship("Truck", secondary=driver_trucks, back_populates="qualified_drivers")

    documents = relationship(
        "Document",
        primaryjoin="and_(Document.entity_id == foreign(Driver.id), Document.entity_type == 'driver')",
        viewonly=True,
        lazy="select"
    )
    allocations = relationship("LoadAllocation", back_populates="driver")

    def __repr__(self):
        return f"<Driver {self.first_name} {self.last_name}>"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_license_valid(self) -> bool:
        """Check if the driver's license has not expired."""
        return self.license_expiry >= date.today()

    @property
    def is_allocatable(self) -> bool:
        """Check if driver can be assigned to a load."""
        return (
            self.status == DriverStatus.AVAILABLE
            and self.is_available
            and self.is_license_valid
            and not self.is_deleted
        )
