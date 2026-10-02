"""User-scoped assumption persistence with provenance checks."""

from typing import Any
from uuid import UUID

from sqlalchemy import select

from services.persistence.models import AssumptionModel, EvidenceModel, ScenarioModel
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository


class SqlAlchemyAssumptionRepository(UserOwnedSqlAlchemyRepository):
    model = AssumptionModel

    def create(self, user_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
        self._require_user(user_id)
        payload = dict(values)
        payload.pop("user_id", None)
        payload.pop("id", None)
        evidence_id = payload.get("evidence_id")
        if payload.get("source_type") == "research" and evidence_id is None:
            raise ValueError("research assumptions require evidence_id")
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
        if evidence_id is not None:
            evidence = self._session.scalar(
                select(EvidenceModel).where(
                    EvidenceModel.id == evidence_id,
                    EvidenceModel.user_id == user_id,
                )
            )
            if evidence is None:
                raise ValueError("evidence does not belong to user")
        return super().create(user_id, payload)