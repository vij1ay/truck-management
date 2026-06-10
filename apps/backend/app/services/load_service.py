from datetime import date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models import Load, LoadStatus, LoadHistory, EventCategory, ALLOWED_TRANSITIONS
from app.repositories import LoadRepository, LoadHistoryRepository
from app.schemas.load import LoadCreate, LoadUpdate
from app.services.audit_service import AuditService


class LoadService:
    """Service for load booking and lifecycle management."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID | None = None,
        current_user_id: UUID | None = None,
        is_superadmin: bool = False,
        current_user_roles: list[str] | None = None,
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        self.is_superadmin = is_superadmin
        self.current_user_roles = current_user_roles or []
        self.load_repo = LoadRepository(db, tenant_id)
        self.history_repo = LoadHistoryRepository(db)
        self.audit_service = AuditService(db, tenant_id)

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _is_tenant_admin(self) -> bool:
        return self.is_superadmin or "TenantAdmin" in self.current_user_roles

    def _generate_load_no(self, year: int, seq_no: int) -> str:
        """Format: LD-YYYY-NNNNNN (zero-padded to 6 digits)."""
        return f"LD-{year}-{seq_no:06d}"

    def _add_history(
        self,
        load: Load,
        from_status: LoadStatus | None,
        to_status: LoadStatus,
        remarks: str | None = None,
    ) -> None:
        """Insert an immutable history record for this status transition."""
        entry = LoadHistory(
            load_id=load.id,
            from_status=from_status,
            to_status=to_status,
            changed_by=self.current_user_id,
            remarks=remarks,
            changed_at=datetime.utcnow(),
        )
        self.db.add(entry)

    # ── Public methods ─────────────────────────────────────────────────────────

    def get_load(self, load_id: UUID) -> Load:
        """Fetch a load ensuring tenant isolation."""
        load = self.load_repo.get_active_by_id(load_id)
        if not load:
            raise NotFoundException("Load not found")
        if not self.is_superadmin and load.tenant_id != self.tenant_id:
            raise ForbiddenException("Cannot access load from another tenant")
            
        # If Driver, can only access allocated loads
        if "Driver" in self.current_user_roles and not self._is_tenant_admin():
            from app.repositories.driver import DriverRepository
            driver_repo = DriverRepository(self.db, self.tenant_id)
            driver = driver_repo.get_by_user_id(self.current_user_id)
            if not driver or load.allocated_driver_id != driver.id:
                raise ForbiddenException("Cannot access load not assigned to you")
                
        return load

    def get_loads(
        self,
        page: int = 1,
        size: int = 50,
        status: LoadStatus | None = None,
        client_id: UUID | None = None,
        pickup_date_from: date | None = None,
        pickup_date_to: date | None = None,
        goods_type: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Load], int]:
        """Return paginated, filtered loads."""
        driver_id = None
        if "Driver" in self.current_user_roles and not self._is_tenant_admin():
            from app.repositories.driver import DriverRepository
            driver_repo = DriverRepository(self.db, self.tenant_id)
            driver = driver_repo.get_by_user_id(self.current_user_id)
            if not driver:
                return [], 0
            driver_id = driver.id

        skip = (page - 1) * size
        loads = self.load_repo.get_all_filtered(
            skip=skip, limit=size,
            status=status, client_id=client_id, driver_id=driver_id,
            pickup_date_from=pickup_date_from, pickup_date_to=pickup_date_to,
            goods_type=goods_type, search=search,
        )
        total = self.load_repo.count_filtered(
            status=status, client_id=client_id, driver_id=driver_id,
            pickup_date_from=pickup_date_from, pickup_date_to=pickup_date_to,
            goods_type=goods_type, search=search,
        )
        return loads, total

    def create_load(
        self,
        data: LoadCreate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Load:
        """
        Create a new load booking.
        - Checks for duplicate bookings (same client+route+date).
        - Auto-generates unique load_no (LD-YYYY-NNNNNN) per tenant.
        - Records initial DRAFT history entry.
        """
        # Duplicate booking prevention
        if self.load_repo.check_duplicate_booking(
            client_id=data.client_id,
            origin=data.origin,
            destination=data.destination,
            pickup_date=data.pickup_date,
        ):
            raise ConflictException(
                "A load booking already exists for this client, route, and date"
            )

        # Generate sequential load number
        year = date.today().year
        seq_no = self.load_repo.get_next_seq_no(year)
        load_no = self._generate_load_no(year, seq_no)

        load_data = data.model_dump()
        load_data["load_no"] = load_no
        load_data["load_seq_no"] = seq_no
        load_data["status"] = LoadStatus.DRAFT
        load_data["booked_by"] = self.current_user_id

        load = self.load_repo.create(load_data)

        # Record initial history entry (no from_status for creation)
        self._add_history(load, from_status=None, to_status=LoadStatus.DRAFT,
                          remarks="Load created")

        self.audit_service.log_event(
            event_type="LOAD_CREATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Load",
            resource_id=load.id,
            new_value={"load_no": load_no, "client_id": str(data.client_id)},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.load_repo.get_active_by_id(load.id)

    def update_load(
        self,
        load_id: UUID,
        data: LoadUpdate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Load:
        """
        Update load metadata.
        Only DRAFT and CONFIRMED loads may be edited.
        """
        load = self.get_load(load_id)

        if not load.is_editable:
            raise BadRequestException(
                f"Load in status '{load.status}' cannot be edited. "
                "Only DRAFT and CONFIRMED loads are editable."
            )

        old_status = load.status
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)

        self.load_repo.update(load, update_data)

        self.audit_service.log_event(
            event_type="LOAD_UPDATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Load",
            resource_id=load_id,
            old_value={"status": old_status},
            new_value=update_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.load_repo.get_active_by_id(load_id)

    def transition_status(
        self,
        load_id: UUID,
        to_status: LoadStatus,
        remarks: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Load:
        """
        Transition a load's status following the allowed state machine.
        IN_TRANSIT → CANCELLED requires TenantAdmin or SuperAdmin.
        """
        load = self.get_load(load_id)
        from_status = load.status

        # Validate transition is allowed
        if not load.can_transition_to(to_status):
            allowed = [s.value for s in ALLOWED_TRANSITIONS.get(from_status, [])]
            raise BadRequestException(
                f"Cannot transition from '{from_status}' to '{to_status}'. "
                f"Allowed transitions: {allowed or ['none (terminal state)']}"
            )

        # Extra guard: IN_TRANSIT → CANCELLED requires TenantAdmin
        if from_status == LoadStatus.IN_TRANSIT and to_status == LoadStatus.CANCELLED:
            if not self._is_tenant_admin():
                raise ForbiddenException(
                    "Cancelling an in-transit load requires TenantAdmin approval"
                )

        # Apply transition
        load.status = to_status
        if to_status == LoadStatus.CANCELLED:
            load.cancelled_by = self.current_user_id
            load.cancellation_reason = remarks
            load.cancelled_at = datetime.utcnow()
        elif to_status == LoadStatus.DELIVERED:
            load.actual_delivery_date = date.today()

        self._add_history(load, from_status=from_status, to_status=to_status,
                          remarks=remarks)

        self.audit_service.log_event(
            event_type="LOAD_STATUS_CHANGED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Load",
            resource_id=load_id,
            old_value={"status": from_status},
            new_value={"status": to_status, "remarks": remarks},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Auto-create draft invoice on delivery
        if to_status == LoadStatus.DELIVERED:
            from app.services.invoice_service import InvoiceService
            InvoiceService(
                db=self.db,
                tenant_id=self.tenant_id,
                current_user_id=self.current_user_id,
            ).create_from_load(load)

        self.db.commit()
        return self.load_repo.get_active_by_id(load_id)

    def cancel_load(
        self,
        load_id: UUID,
        reason: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Load:
        """Convenience method to cancel a load with a reason."""
        return self.transition_status(
            load_id=load_id,
            to_status=LoadStatus.CANCELLED,
            remarks=reason,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def delete_load(
        self,
        load_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Soft-delete a load.
        Requires TenantAdmin or SuperAdmin.
        Only DRAFT or CANCELLED loads can be deleted.
        """
        load = self.get_load(load_id)

        if not self._is_tenant_admin():
            raise ForbiddenException("Only TenantAdmin can delete loads")

        if not load.is_deletable:
            raise BadRequestException(
                f"Load in status '{load.status}' cannot be deleted. "
                "Only DRAFT and CANCELLED loads may be deleted."
            )

        self.load_repo.soft_delete(load)

        self.audit_service.log_event(
            event_type="LOAD_DELETED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Load",
            resource_id=load_id,
            old_value={"load_no": load.load_no, "is_deleted": False},
            new_value={"is_deleted": True},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()

    def get_load_history(self, load_id: UUID) -> list[LoadHistory]:
        """Fetch the full history trail for a load."""
        # Validate access first
        self.get_load(load_id)
        return self.history_repo.get_by_load_id(load_id)
