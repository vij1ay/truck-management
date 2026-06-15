import enum
from sqlalchemy import Column, String, Boolean, Numeric, Integer, ForeignKey, Text, Enum as SAEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ClientType(str, enum.Enum):
    COMPANY = "company"
    INDIVIDUAL = "individual"


class Client(BaseModel):
    """Client/Customer model with billing and contact info."""

    __tablename__ = "clients"

    __table_args__ = (
        # A portal login (user_id) may be linked to at most one Client per tenant —
        # but the SAME login can have a separate Client/relationship in another
        # tenant (a shipper can work with multiple carriers). Multiple NULL
        # user_id values are allowed (Postgres treats NULLs as distinct).
        UniqueConstraint("tenant_id", "user_id", name="uq_clients_tenant_user_id"),
    )

    # Multi-tenant
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Classification
    client_type = Column(
        SAEnum(ClientType, name="clienttype", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ClientType.COMPANY
    )

    # Portal login — links this Client (company) to a User account with role "Client".
    # NOT globally unique: the same user can be linked to a Client in more than one
    # tenant (see uq_clients_tenant_user_id above).
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Identity
    company_name = Column(String(255), nullable=False, index=True)
    contact_person = Column(String(200), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=False)
    alternate_phone = Column(String(20), nullable=True)

    # Address
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)

    # Tax / Legal
    gst_no = Column(String(20), nullable=True)
    pan_no = Column(String(20), nullable=True)

    # Billing terms
    credit_limit = Column(Numeric(15, 2), nullable=True, default=0)
    payment_terms_days = Column(Integer, nullable=True, default=30)

    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)

    # Profile picture / logo — relative path under settings.UPLOAD_DIR, served via
    # GET /clients/{id}/avatar (see app/core/avatar_storage.py). Never exposed directly.
    avatar_path = Column(String(512), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="clients")
    user = relationship("User", foreign_keys=[user_id])
    documents = relationship(
        "Document",
        primaryjoin="and_(Document.entity_id == foreign(Client.id), Document.entity_type == 'client')",
        viewonly=True,
        lazy="select"
    )

    loads = relationship("Load", back_populates="client", lazy="dynamic")

    def __repr__(self):
        return f"<Client {self.company_name}>"

    @property
    def has_avatar(self) -> bool:
        """Whether a profile picture / logo has been uploaded for this client."""
        return bool(self.avatar_path)
