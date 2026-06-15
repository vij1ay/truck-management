from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenPayloadSchema,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirm,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserBasic,
    UserResponse,
    UserListResponse,
    UserActivateRequest,
    TimezoneListResponse,
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
    TruckPhotoResponse,
    TruckBasic,
)
from app.schemas.driver import (
    DriverCreate,
    DriverUpdate,
    DriverResponse,
    DriverMeResponse,
    DriverListResponse,
    DriverAvailabilityUpdate,
)
from app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse,
    LinkPortalAccountRequest,
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
    LoadCheckpointRequest,
    LoadResponse,
    LoadListResponse,
    LoadHistoryResponse,
    PortalLoadCreate,
    PortalLoadResponse,
    PortalLoadListResponse,
)
from app.schemas.portal import (
    PortalCarrierLink,
    PortalProfileResponse,
    PortalInvoiceResponse,
    PortalInvoiceListResponse,
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
    "PasswordResetResponse",
    "PasswordResetConfirm",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserBasic",
    "UserResponse",
    "UserListResponse",
    "UserActivateRequest",
    "TimezoneListResponse",
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
    "TruckPhotoResponse",
    "TruckBasic",
    # Driver
    "DriverCreate",
    "DriverUpdate",
    "DriverResponse",
    "DriverMeResponse",
    "DriverListResponse",
    "DriverAvailabilityUpdate",
    # Client
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    "ClientListResponse",
    "LinkPortalAccountRequest",
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
    "LoadCheckpointRequest",
    "LoadResponse",
    "LoadListResponse",
    "LoadHistoryResponse",
    "PortalLoadCreate",
    "PortalLoadResponse",
    "PortalLoadListResponse",
    "PortalCarrierLink",
    "PortalProfileResponse",
    "PortalInvoiceResponse",
    "PortalInvoiceListResponse",
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

