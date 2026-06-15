from datetime import datetime
from uuid import UUID

from sqlalchemy import select, and_, update
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models import PasswordResetToken
from app.repositories.base import BaseRepository


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    """Repository for password-reset token operations (mirrors RefreshTokenRepository)."""

    def __init__(self, db: Session):
        super().__init__(PasswordResetToken, db)

    def create_token(self, user_id: UUID, token_hash: str, expires_at: datetime) -> PasswordResetToken:
        token = PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(token)
        self.db.flush()
        return token

    def get_valid_token(self, token_hash: str) -> PasswordResetToken | None:
        """Get a valid (unused, non-expired) reset token by its hash."""
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > utc_now(),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def mark_used(self, token: PasswordResetToken) -> None:
        token.mark_used()
        self.db.flush()

    def invalidate_all_for_user(self, user_id: UUID) -> int:
        """Mark any outstanding (unused, unexpired) tokens for this user as used —
        requesting a new reset invalidates older ones."""
        stmt = (
            update(PasswordResetToken)
            .where(
                and_(
                    PasswordResetToken.user_id == user_id,
                    PasswordResetToken.used_at.is_(None),
                )
            )
            .values(used_at=utc_now())
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return result.rowcount
