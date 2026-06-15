from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.logger import get_logger
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.middleware.tenant_context import get_client_ip
from app.models import User
from app.schemas import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    MessageResponse,
    UserBasic,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirm,
)
from app.services import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)
settings = get_settings()


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    data: LoginRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Authenticate a user and return access/refresh tokens.
    
    - Rate limited: 5 requests per minute per IP
    - Returns JWT access token and refresh token
    - Access token expires in 15 minutes
    - Refresh token expires in 7 days
    """
    auth_service = AuthService(db)
    logger.info(f"Login attempt email={data.email} ip={get_client_ip(request)}")
    
    user, access_token, refresh_token, expires_in = auth_service.authenticate(
        email=data.email,
        password=data.password,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    logger.info(f"Login succeeded user_id={user.id}")
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=UserBasic(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            tenant_id=user.tenant_id
        )
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: Request,
    data: TokenRefreshRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Refresh access and refresh tokens.
    
    - Requires a valid refresh token
    - Old refresh token is revoked (token rotation)
    - Returns new access and refresh tokens
    """
    auth_service = AuthService(db)
    logger.info("Refresh token request received")
    
    access_token, new_refresh_token, expires_in = auth_service.refresh_tokens(
        refresh_token=data.refresh_token,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    logger.info("Refresh token issued")
    
    return TokenRefreshResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in
    )


@router.post("/logout", response_model=MessageResponse, status_code=200)
async def logout(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Logout the current user.
    
    - Requires authentication
    - Revokes all refresh tokens for the user
    """
    auth_service = AuthService(db)
    logger.info(f"Logout requested user_id={current_user.id}")
    
    auth_service.logout(
        user=current_user,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )
    
    return MessageResponse(message="Successfully logged out")


@router.post("/logout-all", response_model=MessageResponse, status_code=200)
async def logout_all_sessions(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Logout from all sessions.

    - Requires authentication
    - Revokes all refresh tokens across all devices
    """
    auth_service = AuthService(db)
    logger.info(f"Logout-all requested user_id={current_user.id}")

    count = auth_service.logout_all_sessions(
        user=current_user,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )

    return MessageResponse(message=f"Successfully logged out from {count} sessions")


@router.post("/forgot-password", response_model=PasswordResetResponse, status_code=200)
async def forgot_password(
    request: Request,
    data: PasswordResetRequest,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Request a password reset.

    Always returns the same generic message, whether or not the email matches an
    account, to avoid email enumeration. There is no email service yet — when
    `DEBUG=true`, the raw reset token is also returned directly in the response so
    the flow can be exercised end-to-end (use it as `?token=...` on
    POST /auth/reset-password).
    """
    auth_service = AuthService(db)
    logger.info(f"Password reset requested email={data.email} ip={get_client_ip(request)}")

    raw_token = auth_service.request_password_reset(
        email=data.email,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )

    response = PasswordResetResponse(
        message="If an account exists for this email, a password reset link has been generated."
    )
    if settings.DEBUG and raw_token:
        response.reset_token = raw_token
    return response


@router.post("/reset-password", response_model=MessageResponse, status_code=200)
async def reset_password(
    request: Request,
    data: PasswordResetConfirm,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Complete a password reset using a token from POST /auth/forgot-password.

    - Token is single-use and expires after 1 hour
    - All existing sessions (refresh tokens) are revoked on success
    """
    auth_service = AuthService(db)
    logger.info(f"Password reset confirm ip={get_client_ip(request)}")

    auth_service.reset_password(
        token=data.token,
        new_password=data.new_password,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent")
    )

    return MessageResponse(message="Password has been reset successfully. Please log in with your new password.")
