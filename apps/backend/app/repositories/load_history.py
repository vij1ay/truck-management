from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.load import LoadHistory
from app.repositories.base import BaseRepository


class LoadHistoryRepository(BaseRepository[LoadHistory]):
    """Repository for load history (immutable audit trail)."""

    def __init__(self, db: Session):
        super().__init__(LoadHistory, db)

    def get_by_load_id(self, load_id: UUID) -> list[LoadHistory]:
        """Retrieve all history entries for a load, ordered chronologically."""
        stmt = (
            select(LoadHistory)
            .where(LoadHistory.load_id == load_id)
            .order_by(LoadHistory.changed_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())
