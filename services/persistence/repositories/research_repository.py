"""User-scoped research query and source metadata repositories."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.persistence.models import ResearchQueryModel, ResearchSourceModel
from services.persistence.repositories.base import require_user_transaction, to_record


class SqlAlchemyResearchRepository:
    def __init__(self, session: Session, user_id: UUID) -> None:
        self._session = session
        self._user_id = user_id

    def _require_user(self, user_id: UUID) -> None:
        require_user_transaction(self._session, user_id, self._user_id)

    def create_query(self, user_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
        self._require_user(user_id)
        payload = dict(values)
        payload.pop("user_id", None)
        payload.pop("id", None)
        entity = ResearchQueryModel(user_id=user_id, **payload)
        self._session.add(entity)
        self._session.flush()
        return to_record(entity)

    def get_query(self, user_id: UUID, query_id: UUID) -> dict[str, Any] | None:
        self._require_user(user_id)
        entity = self._session.scalar(
            select(ResearchQueryModel).where(
                ResearchQueryModel.id == query_id,
                ResearchQueryModel.user_id == user_id,
            )
        )
        return to_record(entity) if entity is not None else None

    def list_queries(self, user_id: UUID) -> list[dict[str, Any]]:
        self._require_user(user_id)
        entities = self._session.scalars(
            select(ResearchQueryModel)
            .where(ResearchQueryModel.user_id == user_id)
            .order_by(ResearchQueryModel.created_at)
        )
        return [to_record(entity) for entity in entities]

    def create_source(
        self,
        user_id: UUID,
        research_query_id: UUID,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        self._require_user(user_id)
        if self.get_query(user_id, research_query_id) is None:
            raise ValueError("research query does not belong to user")
        payload = dict(values)
        payload.pop("research_query_id", None)
        payload.pop("id", None)
        entity = ResearchSourceModel(research_query_id=research_query_id, **payload)
        self._session.add(entity)
        self._session.flush()
        return to_record(entity)

    def list_sources(self, user_id: UUID, research_query_id: UUID) -> list[dict[str, Any]]:
        self._require_user(user_id)
        entities = self._session.scalars(
            select(ResearchSourceModel)
            .join(
                ResearchQueryModel,
                ResearchQueryModel.id == ResearchSourceModel.research_query_id,
            )
            .where(
                ResearchSourceModel.research_query_id == research_query_id,
                ResearchQueryModel.user_id == user_id,
            )
            .order_by(ResearchSourceModel.created_at)
        )
        return [to_record(entity) for entity in entities]