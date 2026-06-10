from typing import Any

from app.core.logger import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Base exception for application errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str | None = None,
        details: dict[str, Any] | None = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        self.details = details or {}
        super().__init__(self.message)
        
        # Log the exception
        log_msg = f"{self.error_code}: {self.message}"
        if self.details:
            log_msg += f" | details={self.details}"
        
        if status_code >= 500:
            logger.error(log_msg)
        elif status_code >= 400:
            logger.warning(log_msg)


class UnauthorizedException(AppException):
    """Exception for authentication failures."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        error_code: str = "UNAUTHORIZED",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code=error_code,
            details=details
        )


class ForbiddenException(AppException):
    """Exception for authorization failures."""
    
    def __init__(
        self,
        message: str = "Access denied",
        error_code: str = "FORBIDDEN",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
            details=details
        )


class NotFoundException(AppException):
    """Exception for resource not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=404,
            error_code=error_code,
            details=details
        )


class BadRequestException(AppException):
    """Exception for invalid requests."""
    
    def __init__(
        self,
        message: str = "Invalid request",
        error_code: str = "BAD_REQUEST",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code=error_code,
            details=details
        )


class ConflictException(AppException):
    """Exception for resource conflicts."""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        error_code: str = "CONFLICT",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code=error_code,
            details=details
        )


class TooManyRequestsException(AppException):
    """Exception for rate limiting."""
    
    def __init__(
        self,
        message: str = "Too many requests",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        retry_after: int | None = None,
        details: dict[str, Any] | None = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            status_code=429,
            error_code=error_code,
            details=details
        )


class AccountLockedException(AppException):
    """Exception for locked accounts."""
    
    def __init__(
        self,
        message: str = "Account is locked",
        error_code: str = "ACCOUNT_LOCKED",
        locked_until: str | None = None,
        details: dict[str, Any] | None = None
    ):
        details = details or {}
        if locked_until:
            details["locked_until"] = locked_until
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
            details=details
        )


class TenantInactiveException(AppException):
    """Exception for inactive tenant access."""
    
    def __init__(
        self,
        message: str = "Tenant is inactive",
        error_code: str = "TENANT_INACTIVE",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code=error_code,
            details=details
        )


class TokenExpiredException(UnauthorizedException):
    """Exception for expired tokens."""
    
    def __init__(
        self,
        message: str = "Token has expired",
        error_code: str = "TOKEN_EXPIRED",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


class InvalidTokenException(UnauthorizedException):
    """Exception for invalid tokens."""
    
    def __init__(
        self,
        message: str = "Invalid token",
        error_code: str = "INVALID_TOKEN",
        details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )
