from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenPayloadSchema,
    PasswordChangeRequest,
    PasswordResetRequest,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserBasic,
    UserResponse,
    UserListResponse,
    UserActivateRequest,
    RoleBasic,
)
from app.schemas.tenant import (
    TenantBase,
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
)
from app.schemas.role import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
    RoleAssignmentRequest,
    RoleAssignmentResponse,
)
from app.schemas.audit_log import (
    AuditLogResponse,
    AuditLogFilter,
    AuditLogListResponse,
)
from app.schemas.common import (
    PaginationParams,
    MessageResponse,
    ErrorResponse,
    HealthResponse,
)
from app.schemas.truck import (
    TruckCreate,
    TruckUpdate,
    TruckResponse,
    TruckListResponse,
)
from app.schemas.driver import (
    DriverCreate,
    DriverUpdate,
    DriverResponse,
    DriverListResponse,
    DriverAvailabilityUpdate,
)
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse,
)
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    ExpiringDocumentResponse,
)
from app.schemas.load import (
    LoadCreate,
    LoadUpdate,
    LoadStatusTransition,
    LoadCancelRequest,
    LoadResponse,
    LoadListResponse,
    LoadHistoryResponse,
)
from app.schemas.invoice import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceListResponse,
    PaymentCreate, PaymentResponse,
)
from app.schemas.allocation import (
    AllocationCreate,
    AllocationUpdate,
    DeallocationRequest,
    AllocationResponse,
    AvailableTrucksResponse,
    AvailableDriversResponse,
)

__all__ = [
    # Auth
    "LoginRequest",
    "LoginResponse",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    "TokenPayloadSchema",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserBasic",
    "UserResponse",
    "UserListResponse",
    "UserActivateRequest",
    "RoleBasic",
    # Tenant
    "TenantBase",
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantListResponse",
    # Role
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RoleListResponse",
    "RoleAssignmentRequest",
    "RoleAssignmentResponse",
    # Audit Log
    "AuditLogResponse",
    "AuditLogFilter",
    "AuditLogListResponse",
    # Common
    "PaginationParams",
    "MessageResponse",
    "ErrorResponse",
    "HealthResponse",
    # Truck
    "TruckCreate",
    "TruckUpdate",
    "TruckResponse",
    "TruckListResponse",
    # Driver
    "DriverCreate",
    "DriverUpdate",
    "DriverResponse",
    "DriverListResponse",
    "DriverAvailabilityUpdate",
    # Client
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    "ClientListResponse",
    # Document
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentListResponse",
    "ExpiringDocumentResponse",
    # Load
    "LoadCreate",
    "LoadUpdate",
    "LoadStatusTransition",
    "LoadCancelRequest",
    "LoadResponse",
    "LoadListResponse",
    "LoadHistoryResponse",
    # Invoice
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceResponse",
    "InvoiceListResponse",
    "PaymentCreate",
    "PaymentResponse",
    # Allocation
    "AllocationCreate",
    "AllocationUpdate",
    "DeallocationRequest",
    "AllocationResponse",
    "AvailableTrucksResponse",
    "AvailableDriversResponse",
]

