from app.repositories.base import BaseRepository, TenantAwareRepository
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository
from app.repositories.role import RoleRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.password_reset_token import PasswordResetTokenRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.truck import TruckRepository
from app.repositories.truck_photo import TruckPhotoRepository
from app.repositories.driver import DriverRepository
from app.repositories.client import ClientRepository
from app.repositories.document import DocumentRepository
from app.repositories.load import LoadRepository
from app.repositories.load_history import LoadHistoryRepository
from app.repositories.allocation import AllocationRepository
from app.repositories.invoice import InvoiceRepository, PaymentRepository

__all__ = [
    "BaseRepository",
    "TenantAwareRepository",
    "TenantRepository",
    "UserRepository",
    "RoleRepository",
    "RefreshTokenRepository",
    "PasswordResetTokenRepository",
    "AuditLogRepository",
    "TruckRepository",
    "TruckPhotoRepository",
    "DriverRepository",
    "ClientRepository",
    "DocumentRepository",
    "LoadRepository",
    "LoadHistoryRepository",
    "AllocationRepository",
    "InvoiceRepository",
    "PaymentRepository",
]

