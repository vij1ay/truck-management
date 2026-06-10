import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.dependencies.auth import get_current_user_context, require_roles, CurrentUser
from app.dependencies.database import get_db
from app.middleware.tenant_context import get_client_ip
from app.models import User, Client, ClientType, EntityType
from app.schemas import (
    ClientCreate, ClientUpdate, ClientResponse, ClientListResponse,
    DocumentCreate, DocumentResponse, DocumentListResponse,
)
from app.services import ClientService, DocumentService

router = APIRouter(prefix="/clients", tags=["Clients"])
logger = get_logger(__name__)


def get_client_service(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ClientService:
    return ClientService(
        db=db,
        tenant_id=context.tenant_id,
        current_user_id=context.user_id,
        is_superadmin=context.is_superadmin,
    )


def get_doc_service(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> DocumentService:
    return DocumentService(
        db=db,
        tenant_id=context.tenant_id,
        current_user_id=context.user_id,
        is_superadmin=context.is_superadmin,
    )


@router.get("", response_model=ClientListResponse)
async def list_clients(
    service: Annotated[ClientService, Depends(get_client_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    client_type: ClientType | None = None,
    is_active: bool | None = None,
    search: str | None = None,
):
    """List clients with optional filters (paginated)."""
    logger.info(f"List clients page={page} size={size} client_type={client_type} active={is_active}")
    clients, total = service.get_clients(
        page=page, size=size, client_type=client_type,
        is_active=is_active, search=search,
    )
    return ClientListResponse(
        items=clients, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(
    request: Request,
    data: ClientCreate,
    service: Annotated[ClientService, Depends(get_client_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Create a new client."""
    logger.info(f"Create client name={data.company_name}")
    client = service.create_client(
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return client


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    service: Annotated[ClientService, Depends(get_client_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts", "Client"))],
):
    """Get a client by ID."""
    logger.info(f"Get client client_id={client_id}")
    return service.get_client(client_id)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    request: Request,
    client_id: UUID,
    data: ClientUpdate,
    service: Annotated[ClientService, Depends(get_client_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Update a client."""
    logger.info(f"Update client client_id={client_id}")
    return service.update_client(
        client_id=client_id, data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    request: Request,
    client_id: UUID,
    service: Annotated[ClientService, Depends(get_client_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin"))],
):
    """Soft delete a client. Requires TenantAdmin."""
    logger.info(f"Delete client client_id={client_id}")
    service.delete_client(
        client_id=client_id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )


@router.get("/{client_id}/documents", response_model=DocumentListResponse)
async def list_client_documents(
    client_id: UUID,
    service: Annotated[ClientService, Depends(get_client_service)],
    doc_service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts"))],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    """List all documents for a specific client."""
    logger.info(f"List client documents client_id={client_id} page={page} size={size}")
    service.get_client(client_id)
    docs, total = doc_service.get_documents(
        page=page, size=size,
        entity_type=EntityType.CLIENT,
        entity_id=client_id,
    )
    return DocumentListResponse(
        items=docs, total=total, page=page, size=size,
        pages=math.ceil(total / size) if total > 0 else 1,
    )


@router.post("/{client_id}/documents", response_model=DocumentResponse, status_code=201)
async def add_client_document(
    request: Request,
    client_id: UUID,
    data: DocumentCreate,
    service: Annotated[ClientService, Depends(get_client_service)],
    doc_service: Annotated[DocumentService, Depends(get_doc_service)],
    _: Annotated[User, Depends(require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin"))],
):
    """Upload/add a document for a client."""
    from app.core.exceptions import BadRequestException

    service.get_client(client_id)

    if data.entity_id != client_id or data.entity_type != EntityType.CLIENT:
        raise BadRequestException("entity_id and entity_type must match the client")

    logger.info(f"Add client document client_id={client_id} document_type={data.document_type}")
    return doc_service.create_document(
        data=data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
