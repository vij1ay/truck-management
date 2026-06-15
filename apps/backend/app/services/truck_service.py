from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    ForbiddenException,
)
from app.core.avatar_storage import validate_image, save_avatar, delete_avatar, read_avatar
from app.models import Truck, TruckStatus, TruckPhoto, EventCategory
from app.repositories import TruckRepository, DocumentRepository, TruckPhotoRepository
from app.schemas.truck import TruckCreate, TruckUpdate
from app.services.audit_service import AuditService


class TruckService:
    """Service for truck management operations."""

    MAX_PHOTOS = 6

    def __init__(
        self,
        db: Session,
        tenant_id: UUID | None = None,
        current_user_id: UUID | None = None,
        is_superadmin: bool = False,
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.is_superadmin = is_superadmin
        self.truck_repo = TruckRepository(db, tenant_id)
        self.doc_repo = DocumentRepository(db, tenant_id)
        self.photo_repo = TruckPhotoRepository(db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    def get_truck(self, truck_id: UUID) -> Truck:
        """Get a truck by ID."""
        truck = self.truck_repo.get_active_by_id(truck_id)
        if not truck:
            raise NotFoundException("Truck not found")
        if not self.is_superadmin and truck.tenant_id != self.tenant_id:
            raise ForbiddenException("Cannot access truck from another tenant")
        return truck

    def upload_avatar(
        self,
        truck_id: UUID,
        content: bytes,
        content_type: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Truck:
        """Validate, store, and attach a profile picture to a truck."""
        truck = self.get_truck(truck_id)
        ext = validate_image(content, content_type)

        old_path = truck.avatar_path
        truck.avatar_path = save_avatar("trucks", content, ext)
        self.db.flush()
        delete_avatar(old_path)

        self.audit_service.log_event(
            event_type="TRUCK_AVATAR_UPDATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=truck.tenant_id,
            resource_type="truck",
            resource_id=truck.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return truck

    def remove_avatar(
        self,
        truck_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Truck:
        """Remove a truck's profile picture, if any."""
        truck = self.get_truck(truck_id)
        delete_avatar(truck.avatar_path)
        truck.avatar_path = None
        self.db.flush()

        self.audit_service.log_event(
            event_type="TRUCK_AVATAR_REMOVED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=truck.tenant_id,
            resource_type="truck",
            resource_id=truck.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return truck

    def get_avatar(self, truck_id: UUID) -> tuple[bytes, str]:
        """Read a truck's stored profile picture."""
        truck = self.get_truck(truck_id)
        if not truck.avatar_path:
            raise NotFoundException("No avatar set for this truck")
        return read_avatar(truck.avatar_path)

    def list_photos(self, truck_id: UUID) -> list[TruckPhoto]:
        """List a truck's photo gallery (ordered by position)."""
        self.get_truck(truck_id)
        return self.photo_repo.get_all_by_truck(truck_id)

    def upload_photo(
        self,
        truck_id: UUID,
        content: bytes,
        content_type: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TruckPhoto:
        """Validate, store, and add a photo to a truck's gallery (max MAX_PHOTOS)."""
        truck = self.get_truck(truck_id)

        count = self.photo_repo.count_by_truck(truck_id)
        if count >= self.MAX_PHOTOS:
            raise BadRequestException(f"Maximum of {self.MAX_PHOTOS} photos allowed per truck")

        ext = validate_image(content, content_type)
        photo_path = save_avatar("truck_photos", content, ext)

        photo = self.photo_repo.create({
            "tenant_id": truck.tenant_id,
            "truck_id": truck.id,
            "photo_path": photo_path,
            "position": count,
        })
        self.db.flush()

        self.audit_service.log_event(
            event_type="TRUCK_PHOTO_ADDED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=truck.tenant_id,
            resource_type="truck_photo",
            resource_id=photo.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return photo

    def remove_photo(
        self,
        truck_id: UUID,
        photo_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Remove a photo from a truck's gallery."""
        truck = self.get_truck(truck_id)

        photo = self.photo_repo.get_by_id(photo_id)
        if not photo or photo.truck_id != truck.id:
            raise NotFoundException("Photo not found")

        delete_avatar(photo.photo_path)
        self.db.delete(photo)
        self.db.flush()

        self.audit_service.log_event(
            event_type="TRUCK_PHOTO_REMOVED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=truck.tenant_id,
            resource_type="truck_photo",
            resource_id=photo_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def get_photo(self, truck_id: UUID, photo_id: UUID) -> tuple[bytes, str]:
        """Read one of a truck's gallery photos."""
        truck = self.get_truck(truck_id)

        photo = self.photo_repo.get_by_id(photo_id)
        if not photo or photo.truck_id != truck.id:
            raise NotFoundException("Photo not found")

        return read_avatar(photo.photo_path)

    def get_trucks(
        self,
        page: int = 1,
        size: int = 50,
        status=None,
        truck_type=None,
        ownership_type=None,
        is_available: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None,
    ) -> tuple[list[Truck], int]:
        """Get paginated list of trucks."""
        skip = (page - 1) * size
        trucks = self.truck_repo.get_all_filtered(
            skip=skip, limit=size,
            status=status, truck_type=truck_type,
            ownership_type=ownership_type,
            is_available=is_available, search=search, tenant_id=tenant_id,
            include_all_tenants=self.is_superadmin,
        )
        total = self.truck_repo.count_filtered(
            status=status, truck_type=truck_type,
            ownership_type=ownership_type,
            is_available=is_available, search=search, tenant_id=tenant_id,
            include_all_tenants=self.is_superadmin,
        )
        return trucks, total

    def create_truck(
        self,
        data: TruckCreate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Truck:
        """Create a new truck."""
        # Registration uniqueness per tenant
        if self.truck_repo.check_registration_conflict(data.registration_no):
            raise ConflictException(
                f"Truck with registration '{data.registration_no}' already exists in this tenant"
            )

        truck_data = data.model_dump()
        truck = self.truck_repo.create(truck_data)

        self.audit_service.log_event(
            event_type="TRUCK_CREATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Truck",
            resource_id=truck.id,
            new_value={"registration_no": truck.registration_no, "truck_type": truck.truck_type},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.truck_repo.get_active_by_id(truck.id)

    def update_truck(
        self,
        truck_id: UUID,
        data: TruckUpdate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Truck:
        """Update a truck."""
        truck = self.get_truck(truck_id)
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)

        old_data = {
            "registration_no": truck.registration_no,
            "status": truck.status,
            "is_available": truck.is_available,
        }

        self.truck_repo.update(truck, update_data)

        self.audit_service.log_event(
            event_type="TRUCK_UPDATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Truck",
            resource_id=truck_id,
            old_value=old_data,
            new_value=update_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.truck_repo.get_active_by_id(truck_id)

    def delete_truck(
        self,
        truck_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Soft delete a truck."""
        truck = self.get_truck(truck_id)
        self.truck_repo.soft_delete(truck)

        self.audit_service.log_event(
            event_type="TRUCK_DELETED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Truck",
            resource_id=truck_id,
            old_value={"registration_no": truck.registration_no, "is_deleted": False},
            new_value={"is_deleted": True},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()

    def activate_truck(
        self,
        truck_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Truck:
        """Activate a truck."""
        truck = self.get_truck(truck_id)
        if truck.status == TruckStatus.ACTIVE:
            raise BadRequestException("Truck is already active")
        if truck.status == TruckStatus.DECOMMISSIONED:
            raise BadRequestException("Decommissioned trucks cannot be reactivated")

        truck.status = TruckStatus.ACTIVE
        truck.is_available = True

        self.audit_service.log_event(
            event_type="TRUCK_ACTIVATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Truck",
            resource_id=truck_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.truck_repo.get_active_by_id(truck_id)

    def deactivate_truck(
        self,
        truck_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Truck:
        """Deactivate a truck (sets to INACTIVE)."""
        truck = self.get_truck(truck_id)
        if truck.status == TruckStatus.INACTIVE:
            raise BadRequestException("Truck is already inactive")

        truck.status = TruckStatus.INACTIVE
        truck.is_available = False

        self.audit_service.log_event(
            event_type="TRUCK_DEACTIVATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Truck",
            resource_id=truck_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.truck_repo.get_active_by_id(truck_id)
