from datetime import datetime
from uuid import UUID

from sqlalchemy import select, and_, update
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for refresh token operations."""
    
    def __init__(self, db: Session):
        super().__init__(RefreshToken, db)
    
    def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Get a refresh token by its hash."""
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_valid_token(self, token_hash: str) -> RefreshToken | None:
        """Get a valid (non-expired, non-revoked) refresh token."""
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > utc_now()
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()
    
    def create_token(
        self,
        user_id: UUID,
        tenant_id: UUID | None,
        token_hash: str,
        expires_at: datetime,
        device_info: str | None = None,
        ip_address: str | None = None
    ) -> RefreshToken:
        """Create a new refresh token."""
        token = RefreshToken(
            user_id=user_id,
            tenant_id=tenant_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address
        )
        self.db.add(token)
        self.db.flush()
        return token
    
    def revoke_token(self, token: RefreshToken) -> None:
        """Revoke a refresh token."""
        token.revoke()
        self.db.flush()
    
    def revoke_all_user_tokens(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user."""
        stmt = (
            update(RefreshToken)
            .where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked == False
                )
            )
            .values(revoked=True, revoked_at=utc_now())
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return result.rowcount
    
    def cleanup_expired_tokens(self) -> int:
        """Delete expired tokens (can be run periodically)."""
        stmt = select(RefreshToken).where(
            RefreshToken.expires_at < utc_now()
        )
        expired = list(self.db.execute(stmt).scalars().all())
        count = len(expired)
        for token in expired:
            self.db.delete(token)
        self.db.flush()
        return count
