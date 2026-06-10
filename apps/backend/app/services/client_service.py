from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    ForbiddenException,
)
from app.models import Client, EventCategory
from app.repositories import ClientRepository
from app.schemas.client import ClientCreate, ClientUpdate
from app.services.audit_service import AuditService


class ClientService:
    """Service for client management operations."""

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
        self.client_repo = ClientRepository(db, tenant_id)
        self.audit_service = AuditService(db, tenant_id)

    def get_client(self, client_id: UUID) -> Client:
        """Get a client by ID."""
        client = self.client_repo.get_active_by_id(client_id)
        if not client:
            raise NotFoundException("Client not found")
        if not self.is_superadmin and client.tenant_id != self.tenant_id:
            raise ForbiddenException("Cannot access client from another tenant")
        return client

    def get_clients(
        self,
        page: int = 1,
        size: int = 50,
        client_type=None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Client], int]:
        """Get paginated list of clients."""
        skip = (page - 1) * size
        clients = self.client_repo.get_all_filtered(
            skip=skip, limit=size,
            client_type=client_type, is_active=is_active, search=search,
        )
        total = self.client_repo.count_filtered(
            client_type=client_type, is_active=is_active, search=search,
        )
        return clients, total

    def create_client(
        self,
        data: ClientCreate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Client:
        """Create a new client."""
        # Email uniqueness if provided
        if data.email and self.client_repo.check_email_conflict(data.email):
            raise ConflictException(f"Client with email '{data.email}' already exists")

        client_data = data.model_dump()
        client = self.client_repo.create(client_data)

        self.audit_service.log_event(
            event_type="CLIENT_CREATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Client",
            resource_id=client.id,
            new_value={
                "company_name": client.company_name,
                "client_type": client.client_type,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.client_repo.get_active_by_id(client.id)

    def update_client(
        self,
        client_id: UUID,
        data: ClientUpdate,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Client:
        """Update a client."""
        client = self.get_client(client_id)
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)

        # Email uniqueness if changing email
        if "email" in update_data and update_data["email"]:
            if self.client_repo.check_email_conflict(update_data["email"], exclude_id=client_id):
                raise ConflictException("Email already in use by another client")

        old_data = {"company_name": client.company_name, "is_active": client.is_active}

        self.client_repo.update(client, update_data)

        self.audit_service.log_event(
            event_type="CLIENT_UPDATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Client",
            resource_id=client_id,
            old_value=old_data,
            new_value=update_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.client_repo.get_active_by_id(client_id)

    def delete_client(
        self,
        client_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Soft delete a client."""
        client = self.get_client(client_id)
        self.client_repo.soft_delete(client)

        self.audit_service.log_event(
            event_type="CLIENT_DELETED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Client",
            resource_id=client_id,
            old_value={"company_name": client.company_name, "is_deleted": False},
            new_value={"is_deleted": True},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
