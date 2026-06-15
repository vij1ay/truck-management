from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.datetime_utils import utc_now
from app.models.base import Base, UUIDMixin, TimestampMixin


class PasswordResetToken(Base, UUIDMixin, TimestampMixin):
    """Single-use, time-limited token for the "forgot password" flow.

    Mirrors RefreshToken's storage pattern: only a SHA-256 hash of the raw
    token is stored (see app.core.security.hash_token), never the raw value.
    """

    __tablename__ = "password_reset_tokens"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<PasswordResetToken user_id={self.user_id} used={self.used_at is not None}>"

    def mark_used(self):
        """Mark this token as used (single-use)."""
        self.used_at = utc_now()
