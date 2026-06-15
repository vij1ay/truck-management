"""Schemas for the customer (Client) portal — `/portal/*` (Phase 11+).

A shipper's portal login can be linked to a separate `Client` (company) record —
and therefore a separate relationship — in more than one tenant (carrier). These
schemas describe that aggregated, multi-carrier view.
"""
from uuid import UUID

from pydantic import BaseModel

from app.schemas.client import ClientResponse
from app.schemas.invoice import InvoiceResponse


class PortalCarrierLink(BaseModel):
    """One of the shipper's carrier relationships."""
    tenant_id: UUID
    tenant_name: str
    client: ClientResponse


class PortalProfileResponse(BaseModel):
    """Response for GET /portal/me — every carrier this login is linked to."""
    carriers: list[PortalCarrierLink]


class PortalInvoiceResponse(InvoiceResponse):
    """An InvoiceResponse plus which carrier (tenant) it belongs to — used when
    the customer portal aggregates invoices across multiple linked carriers."""
    carrier_name: str


class PortalInvoiceListResponse(BaseModel):
    items: list[PortalInvoiceResponse]
    total: int
    page: int
    size: int
    pages: int
