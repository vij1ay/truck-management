from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import (
    UnauthorizedException,
    BadRequestException,
    AccountLockedException,
)
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
    decode_token,
    TokenPayload,
)
from app.models import User, EventCategory
from app.repositories import UserRepository, RefreshTokenRepository
from app.services.audit_service import AuditService

settings = get_settings()


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)
        self.audit_service = AuditService(db)
    
    def authenticate(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> tuple[User, str, str, int]:
        """
        Authenticate a user with email and password.
        
        Returns:
            tuple: (user, access_token, refresh_token, expires_in)
        
        Raises:
            UnauthorizedException: If credentials are invalid
            AccountLockedException: If account is locked
        """
        # Get user by email
        user = self.user_repo.get_by_email(email)
        
        if not user:
            raise UnauthorizedException("Invalid email or password")
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            self.audit_service.log_login(
                user_id=user.id,
                tenant_id=user.tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False
            )
            raise AccountLockedException(
                f"Account is locked until {user.locked_until.isoformat()}",
                locked_until=user.locked_until.isoformat()
            )
        
        # Verify password
        if not verify_password(password, user.password_hash):
            self._handle_failed_login(user, ip_address, user_agent)
            raise UnauthorizedException("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            self.audit_service.log_login(
                user_id=user.id,
                tenant_id=user.tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False
            )
            raise UnauthorizedException("Account is deactivated")
        
        # Check tenant status
        if user.tenant and not user.tenant.is_active:
            self.audit_service.log_login(
                user_id=user.id,
                tenant_id=user.tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False
            )
            raise UnauthorizedException("Tenant is inactive")
        
        # Successful login - reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        
        # Generate tokens
        primary_role = user.primary_role or "User"
        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            role=primary_role
        )
        
        raw_refresh, token_hash, expires_at = create_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id
        )
        
        # Store refresh token
        self.token_repo.create_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=user_agent,
            ip_address=ip_address
        )
        
        # Log successful login
        self.audit_service.log_login(
            user_id=user.id,
            tenant_id=user.tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        
        self.db.commit()
        
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return user, access_token, raw_refresh, expires_in
    
    def _handle_failed_login(
        self,
        user: User,
        ip_address: str | None,
        user_agent: str | None
    ) -> None:
        """Handle a failed login attempt."""
        user.failed_login_attempts += 1
        
        # Lock account after max attempts
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(
                minutes=settings.LOCKOUT_DURATION_MINUTES
            )
            self.audit_service.log_event(
                event_type="ACCOUNT_LOCKED",
                event_category=EventCategory.auth,
                user_id=user.id,
                tenant_id=user.tenant_id,
                resource_type="User",
                resource_id=user.id,
                extra_data={"reason": "max_login_attempts_exceeded"},
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        # Log failed login
        self.audit_service.log_login(
            user_id=user.id,
            tenant_id=user.tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False
        )
        
        self.db.commit()
    
    def refresh_tokens(
        self,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> tuple[str, str, int]:
        """
        Refresh access and refresh tokens.
        
        Returns:
            tuple: (new_access_token, new_refresh_token, expires_in)
        """
        # Hash the provided token
        token_hash = hash_token(refresh_token)
        
        # Find valid token in database
        stored_token = self.token_repo.get_valid_token(token_hash)
        if not stored_token:
            raise UnauthorizedException("Invalid or expired refresh token")
        
        # Get user
        user = self.user_repo.get_with_roles(stored_token.user_id)
        if not user or not user.is_active:
            self.token_repo.revoke_token(stored_token)
            self.db.commit()
            raise UnauthorizedException("User not found or inactive")
        
        # Revoke old refresh token (token rotation)
        self.token_repo.revoke_token(stored_token)
        
        # Generate new tokens
        primary_role = user.primary_role or "User"
        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            role=primary_role
        )
        
        raw_refresh, new_token_hash, expires_at = create_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id
        )
        
        # Store new refresh token
        self.token_repo.create_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            token_hash=new_token_hash,
            expires_at=expires_at,
            device_info=user_agent,
            ip_address=ip_address
        )
        
        self.db.commit()
        
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return access_token, raw_refresh, expires_in
    
    def logout(
        self,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> None:
        """Logout a user by revoking all their refresh tokens."""
        self.token_repo.revoke_all_user_tokens(user.id)
        
        # Log logout
        self.audit_service.log_logout(
            user_id=user.id,
            tenant_id=user.tenant_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
    
    def logout_all_sessions(
        self,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> int:
        """Logout from all sessions by revoking all refresh tokens."""
        count = self.token_repo.revoke_all_user_tokens(user.id)
        
        self.audit_service.log_event(
            event_type="LOGOUT_ALL",
            event_category=EventCategory.auth,
            user_id=user.id,
            tenant_id=user.tenant_id,
            resource_type="User",
            resource_id=user.id,
            extra_data={"sessions_revoked": count},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.commit()
        return count
