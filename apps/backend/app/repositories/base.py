from typing import Generic, TypeVar, Type
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.base import Base, BaseModel

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get_by_id(self, id: UUID) -> ModelType | None:
        """Get a record by ID."""
        return self.db.get(self.model, id)
    
    def get_active_by_id(self, id: UUID) -> ModelType | None:
        """Get a non-deleted record by ID."""
        stmt = select(self.model).where(
            and_(
                self.model.id == id,
                self.model.is_deleted == False
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> list[ModelType]:
        """Get all records with pagination."""
        stmt = select(self.model)
        
        if hasattr(self.model, "is_deleted") and not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)
        
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
    
    def count(self, include_deleted: bool = False) -> int:
        """Count all records."""
        stmt = select(func.count()).select_from(self.model)
        
        if hasattr(self.model, "is_deleted") and not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)
        
        return self.db.execute(stmt).scalar_one()
    
    def create(self, obj_in: dict) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.flush()
        return db_obj
    
    def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        """Update an existing record."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)
        
        if hasattr(db_obj, "updated_at"):
            db_obj.updated_at = utc_now()
        
        self.db.flush()
        return db_obj
    
    def delete(self, db_obj: ModelType) -> None:
        """Hard delete a record."""
        self.db.delete(db_obj)
        self.db.flush()
    
    def soft_delete(self, db_obj: ModelType) -> ModelType:
        """Soft delete a record."""
        if hasattr(db_obj, "soft_delete"):
            db_obj.soft_delete()
            self.db.flush()
        return db_obj
    
    def restore(self, db_obj: ModelType) -> ModelType:
        """Restore a soft-deleted record."""
        if hasattr(db_obj, "restore"):
            db_obj.restore()
            self.db.flush()
        return db_obj


class TenantAwareRepository(BaseRepository[ModelType]):
    """Repository with tenant isolation enforcement."""
    
    def __init__(self, model: Type[ModelType], db: Session, tenant_id: UUID | None = None):
        super().__init__(model, db)
        self.tenant_id = tenant_id
    
    def _apply_tenant_filter(self, stmt):
        """Apply tenant filter to a query."""
        if self.tenant_id and hasattr(self.model, "tenant_id"):
            stmt = stmt.where(self.model.tenant_id == self.tenant_id)
        return stmt
    
    def get_active_by_id(self, id: UUID) -> ModelType | None:
        """Get a non-deleted record by ID with tenant filter."""
        stmt = select(self.model).where(
            and_(
                self.model.id == id,
                self.model.is_deleted == False
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> list[ModelType]:
        """Get all records with tenant filter and pagination."""
        stmt = select(self.model)
        
        if hasattr(self.model, "is_deleted") and not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)
        
        stmt = self._apply_tenant_filter(stmt)
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
    
    def count(self, include_deleted: bool = False) -> int:
        """Count records with tenant filter."""
        stmt = select(func.count()).select_from(self.model)
        
        if hasattr(self.model, "is_deleted") and not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)
        
        stmt = self._apply_tenant_filter(stmt)
        return self.db.execute(stmt).scalar_one()
    
    def create(self, obj_in: dict) -> ModelType:
        """Create a new record with tenant_id."""
        if self.tenant_id and hasattr(self.model, "tenant_id"):
            obj_in["tenant_id"] = self.tenant_id
        return super().create(obj_in)
