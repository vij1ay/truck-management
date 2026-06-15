from uuid import UUID
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session, joinedload

from app.models.client import Client, ClientType
from app.repositories.base import TenantAwareRepository


class ClientRepository(TenantAwareRepository[Client]):
    """Repository for client data access with tenant isolation."""

    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(Client, db, tenant_id)

    def get_by_user_id(self, user_id: UUID) -> Client | None:
        """Get this tenant's client linked to the given portal user ID (if any)."""
        stmt = select(Client).where(
            and_(Client.user_id == user_id, Client.is_deleted == False)
        )
        stmt = self._apply_tenant_filter(stmt)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all_by_user_id(self, user_id: UUID) -> list[Client]:
        """ALL client (company) profiles linked to this user, across every tenant.

        Deliberately NOT tenant-scoped (unlike get_by_user_id) — used only by the
        customer portal (app/api/v1/portal.py) for a user resolving their OWN
        cross-tenant carrier relationships. A shipper can have a separate Client
        record (and relationship) with more than one tenant.
        """
        stmt = (
            select(Client)
            .where(and_(Client.user_id == user_id, Client.is_deleted == False))
            .options(joinedload(Client.tenant))
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def get_all_filtered(
        self,
        skip: int = 0,
        limit: int = 100,
        client_type: ClientType | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None,
        include_all_tenants: bool = False,
    ) -> list[Client]:
        """Get clients with optional filters."""
        stmt = select(Client).where(Client.is_deleted == False)
        if not include_all_tenants:
            stmt = self._apply_tenant_filter(stmt)

        if client_type:
            stmt = stmt.where(Client.client_type == client_type)
        if is_active is not None:
            stmt = stmt.where(Client.is_active == is_active)
        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Client.company_name.ilike(search_term),
                    Client.contact_person.ilike(search_term),
                    Client.phone.ilike(search_term),
                    Client.email.ilike(search_term),
                    Client.gst_no.ilike(search_term),
                )
            )
        if tenant_id is not None:
            stmt = stmt.where(Client.tenant_id == tenant_id)

        stmt = stmt.order_by(Client.company_name.asc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_filtered(
        self,
        client_type: ClientType | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        tenant_id: UUID | None = None,
        include_all_tenants: bool = False,
    ) -> int:
        """Count clients matching filters."""
        stmt = select(func.count()).select_from(Client).where(Client.is_deleted == False)
        if not include_all_tenants:
            stmt = self._apply_tenant_filter(stmt)

        if client_type:
            stmt = stmt.where(Client.client_type == client_type)
        if is_active is not None:
            stmt = stmt.where(Client.is_active == is_active)
        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Client.company_name.ilike(search_term),
                    Client.contact_person.ilike(search_term),
                    Client.phone.ilike(search_term),
                    Client.email.ilike(search_term),
                    Client.gst_no.ilike(search_term),
                )
            )
        if tenant_id is not None:
            stmt = stmt.where(Client.tenant_id == tenant_id)

        return self.db.execute(stmt).scalar_one()

    def check_email_conflict(
        self, email: str, exclude_id: UUID | None = None
    ) -> bool:
        """Check if an email is already in use for another client in this tenant."""
        if not email:
            return False
        stmt = select(func.count()).select_from(Client).where(
            and_(
                Client.is_deleted == False,
                Client.email.ilike(email),
            )
        )
        stmt = self._apply_tenant_filter(stmt)
        if exclude_id:
            stmt = stmt.where(Client.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0
