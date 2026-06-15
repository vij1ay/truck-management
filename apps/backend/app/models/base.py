import uuid
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.core.datetime_utils import utc_now


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    def soft_delete(self):
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = utc_now()
    
    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class UUIDMixin:
    """Mixin for UUID primary key."""
    
    @declared_attr
    def id(cls):
        return Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False
        )


class BaseModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Base model with UUID, timestamps, and soft delete."""
    
    __abstract__ = True


class BaseModelNoSoftDelete(Base, UUIDMixin, TimestampMixin):
    """Base model with UUID and timestamps, without soft delete."""
    
    __abstract__ = True
