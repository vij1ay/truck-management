from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    ForbiddenException,
)
from app.core.avatar_storage import validate_image, save_avatar, delete_avatar, read_avatar
from app.models import Client, EventCategory
from app.repositories import ClientRepository, UserRepository
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

    def upload_avatar(
        self,
        client_id: UUID,
        content: bytes,
        content_type: str | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Client:
        """Validate, store, and attach a profile picture / logo to a client."""
        client = self.get_client(client_id)
        ext = validate_image(content, content_type)

        old_path = client.avatar_path
        client.avatar_path = save_avatar("clients", content, ext)
        self.db.flush()
        delete_avatar(old_path)

        self.audit_service.log_event(
            event_type="CLIENT_AVATAR_UPDATED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=client.tenant_id,
            resource_type="client",
            resource_id=client.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return client

    def remove_avatar(
        self,
        client_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Client:
        """Remove a client's profile picture / logo, if any."""
        client = self.get_client(client_id)
        delete_avatar(client.avatar_path)
        client.avatar_path = None
        self.db.flush()

        self.audit_service.log_event(
            event_type="CLIENT_AVATAR_REMOVED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=client.tenant_id,
            resource_type="client",
            resource_id=client.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return client

    def get_avatar(self, client_id: UUID) -> tuple[bytes, str]:
        """Read a client's stored profile picture / logo."""
        client = self.get_client(client_id)
        if not client.avatar_path:
            raise NotFoundException("No avatar set for this client")
        return read_avatar(client.avatar_path)

    def get_clients(
        self,
        page: int = 1,
        size: int = 50,
        client_type=None,
        is_active: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None,
    ) -> tuple[list[Client], int]:
        """Get paginated list of clients."""
        skip = (page - 1) * size
        clients = self.client_repo.get_all_filtered(
            skip=skip, limit=size,
            client_type=client_type, is_active=is_active, search=search, tenant_id=tenant_id,
            include_all_tenants=self.is_superadmin,
        )
        total = self.client_repo.count_filtered(
            client_type=client_type, is_active=is_active, search=search, tenant_id=tenant_id,
            include_all_tenants=self.is_superadmin,
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

    def link_portal_account(
        self,
        client_id: UUID,
        email: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Client:
        """Link this tenant's Client record to an existing portal-user account by
        email — how a shipper already registered with another tenant gains a
        relationship (and "My Shipments" visibility) with THIS tenant too. The
        reverse direction of the "Linked Client" dropdown on the User form."""
        client = self.get_client(client_id)

        user = UserRepository(self.db).get_by_email(email)  # cross-tenant lookup
        if not user or user.is_deleted:
            raise NotFoundException(f"No portal account found for '{email}'")
        if "Client" not in user.role_names:
            raise BadRequestException("This account does not have portal (Client) access")

        # If this user is already linked to a different client in THIS tenant,
        # unlink it first — flush before relinking to avoid a unique-constraint
        # violation on (tenant_id, user_id), same pattern as UserService._link_client.
        existing = self.client_repo.get_by_user_id(user.id)
        if existing and existing.id != client.id:
            existing.user_id = None
            self.db.flush()

        client.user_id = user.id
        self.db.flush()

        self.audit_service.log_event(
            event_type="CLIENT_PORTAL_ACCOUNT_LINKED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Client",
            resource_id=client.id,
            new_value={"linked_email": email},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.client_repo.get_active_by_id(client.id)

    def unlink_portal_account(
        self,
        client_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Client:
        """Remove the portal-account link from this Client record."""
        client = self.get_client(client_id)
        old_user_id = client.user_id
        client.user_id = None
        self.db.flush()

        self.audit_service.log_event(
            event_type="CLIENT_PORTAL_ACCOUNT_UNLINKED",
            event_category=EventCategory.user_mgmt,
            user_id=self.current_user_id,
            tenant_id=self.tenant_id,
            resource_type="Client",
            resource_id=client.id,
            old_value={"user_id": str(old_user_id) if old_user_id else None},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.commit()
        return self.client_repo.get_active_by_id(client.id)

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
