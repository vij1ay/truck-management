from uuid import UUID
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.models.client import Client, ClientType
from app.repositories.base import TenantAwareRepository


class ClientRepository(TenantAwareRepository[Client]):
    """Repository for client data access with tenant isolation."""

    def __init__(self, db: Session, tenant_id: UUID | None = None):
        super().__init__(Client, db, tenant_id)

    def get_all_filtered(
        self,
        skip: int = 0,
        limit: int = 100,
        client_type: ClientType | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[Client]:
        """Get clients with optional filters."""
        stmt = select(Client).where(Client.is_deleted == False)
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

        stmt = stmt.order_by(Client.company_name.asc()).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_filtered(
        self,
        client_type: ClientType | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count clients matching filters."""
        stmt = select(func.count()).select_from(Client).where(Client.is_deleted == False)
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
