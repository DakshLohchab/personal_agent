"""User-scoped evidence persistence."""

from typing import Any
from uuid import UUID

from sqlalchemy import select

from services.persistence.models import EvidenceModel, ResearchQueryModel, ResearchSourceModel
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository


class SqlAlchemyEvidenceRepository(UserOwnedSqlAlchemyRepository):
    model = EvidenceModel

    def create(self, user_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
        self._require_user(user_id)
        payload = dict(values)
        research_source_id = payload.get("research_source_id")
        if research_source_id is not None:
            source = self._session.scalar(
                select(ResearchSourceModel)
                .join(
                    ResearchQueryModel,
                    ResearchQueryModel.id == ResearchSourceModel.research_query_id,
                )
                .where(
                    ResearchSourceModel.id == research_source_id,
                    ResearchQueryModel.user_id == user_id,
                )
            )
            if source is None:
                raise ValueError("research source does not belong to user")
        return super().create(user_id, payload)