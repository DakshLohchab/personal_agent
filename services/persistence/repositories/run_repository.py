"""User-scoped simulation run persistence."""

from typing import Any
from uuid import UUID

from sqlalchemy import select

from services.persistence.models import RunModel, ScenarioModel
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository


class SqlAlchemyRunRepository(UserOwnedSqlAlchemyRepository):
    model = RunModel

    def create(self, user_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
        self._require_user(user_id)
        payload = dict(values)
        scenario_id = payload.get("scenario_id")
        if scenario_id is not None:
            scenario = self._session.scalar(
                select(ScenarioModel).where(
                    ScenarioModel.id == scenario_id,
                    ScenarioModel.user_id == user_id,
                )
            )
            if scenario is None:
                raise ValueError("scenario does not belong to user")
        return super().create(user_id, payload)