from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModelNoSoftDelete


class TruckPhoto(BaseModelNoSoftDelete):
    """A single photo in a truck's gallery (max 6 per truck, enforced in
    TruckService). Hard-deleted (row + file) when removed — no soft delete."""

    __tablename__ = "truck_photos"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    truck_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trucks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relative path under settings.UPLOAD_DIR, served via
    # GET /trucks/{id}/photos/{photo_id} (see app/core/avatar_storage.py).
    photo_path = Column(String(512), nullable=False)

    # Display order within the gallery (0-based, assigned at upload time).
    position = Column(Integer, default=0, nullable=False)

    # Relationships
    truck = relationship("Truck", back_populates="photos")

    def __repr__(self):
        return f"<TruckPhoto truck_id={self.truck_id} position={self.position}>"
