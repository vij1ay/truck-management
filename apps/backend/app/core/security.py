import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any

import jwt
from jwt import PyJWTError as JWTError
from passlib.context import CryptContext

from app.config import get_settings
from app.core.datetime_utils import utc_now

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_COST_FACTOR
)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_token(token: str) -> str:
    """Hash a token using SHA-256 for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID | None,
    role: str,
    expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = utc_now() + expires_delta

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "role": role,
        "exp": expire,
        "iat": utc_now(),
        "jti": str(uuid.uuid4()),  # Unique token ID for revocation
        "type": "access"
    }
    
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID | None,
    expires_delta: timedelta | None = None
) -> tuple[str, str, datetime]:
    """
    Create a refresh token.
    
    Returns:
        tuple: (raw_token, token_hash, expires_at)
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    expires_at = utc_now() + expires_delta

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "exp": expires_at,
        "iat": utc_now(),
        "jti": str(uuid.uuid4()),
        "type": "refresh"
    }
    
    raw_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    token_hash = hash_token(raw_token)
    
    return raw_token, token_hash, expires_at


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )


def decode_token_unverified(token: str) -> dict[str, Any]:
    """Decode a JWT token without verification (for extracting claims)."""
    return jwt.decode(token, options={"verify_signature": False})


class TokenPayload:
    """Parsed JWT token payload."""
    
    def __init__(self, payload: dict[str, Any]):
        self.sub = uuid.UUID(payload["sub"])
        self.tenant_id = uuid.UUID(payload["tenant_id"]) if payload.get("tenant_id") else None
        self.role = payload.get("role")
        self.exp = datetime.fromtimestamp(payload["exp"])
        self.iat = datetime.fromtimestamp(payload["iat"])
        self.jti = payload.get("jti")
        self.token_type = payload.get("type", "access")
    
    @property
    def user_id(self) -> uuid.UUID:
        """Alias for sub (subject)."""
        return self.sub
    
    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        return utc_now() > self.exp
