"""User-scoped memory persistence with lifecycle-aware retrieval."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select

from services.persistence.models import MemoryModel
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository, to_record


class SqlAlchemyMemoryRepository(UserOwnedSqlAlchemyRepository):
    model = MemoryModel

    def list_valid(
        self, user_id: UUID, memory_types: set[str] | None = None
    ) -> list[dict[str, Any]]:
        self._require_user(user_id)
        now = datetime.now(timezone.utc)
        query = select(self.model).where(
            self.model.user_id == user_id,
            self.model.status == "active",
            (self.model.expires_at.is_(None) | (self.model.expires_at > now)),
        )
        if memory_types:
            query = query.where(self.model.memory_type.in_(memory_types))
        entities = self._session.scalars(
            query.order_by(
                self.model.last_confirmed_at.desc().nullslast(), self.model.updated_at.desc()
            )
        )
        return [to_record(entity) for entity in entities]

    def approve(self, user_id: UUID, memory_id: UUID) -> dict[str, Any] | None:
        self._require_user(user_id)
        entity = self._session.scalar(
            select(self.model).where(
                self.model.id == memory_id,
                self.model.user_id == user_id,
                self.model.status == "candidate",
            )
        )
        if entity is None:
            return None
        entity.status = "active"
        entity.last_confirmed_at = datetime.now(timezone.utc)
        self._session.flush()
        return to_record(entity)

    def forget(self, user_id: UUID, memory_id: UUID) -> bool:
        self._require_user(user_id)
        entity = self._session.scalar(
            select(self.model).where(self.model.id == memory_id, self.model.user_id == user_id)
        )
        if entity is None:
            return False
        entity.status = "deleted"
        self._session.flush()
        return True
