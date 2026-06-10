import enum
from sqlalchemy import Column, String, Boolean, Numeric, Integer, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ClientType(str, enum.Enum):
    COMPANY = "company"
    INDIVIDUAL = "individual"


class Client(BaseModel):
    """Client/Customer model with billing and contact info."""

    __tablename__ = "clients"

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

    # Relationships
    tenant = relationship("Tenant", back_populates="clients")
    documents = relationship(
        "Document",
        primaryjoin="and_(Document.entity_id == foreign(Client.id), Document.entity_type == 'client')",
        viewonly=True,
        lazy="select"
    )

    loads = relationship("Load", back_populates="client", lazy="dynamic")

    def __repr__(self):
        return f"<Client {self.company_name}>"
