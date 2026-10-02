"""User-scoped scenarios, immutable input versions, and delta branches."""

from typing import Any
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from pydantic import BaseModel

from services.persistence.models import (
    ScenarioBranchModel,
    ScenarioModel,
    ScenarioVersionModel,
)
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository, to_record


def _json_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


class SqlAlchemyScenarioRepository(UserOwnedSqlAlchemyRepository):
    model = ScenarioModel

    def __init__(self, session: Session, user_id: UUID) -> None:
        super().__init__(session, user_id)
        self._session = session

    def add_version(
        self,
        user_id: UUID,
        scenario_id: UUID,
        state_snapshot: dict[str, Any],
        scenario_snapshot: dict[str, Any],
        *,
        version_number: int | None = None,
    ) -> dict[str, Any]:
        self._require_user(user_id)
        if self.get(user_id, scenario_id) is None:
            raise ValueError("scenario does not belong to user")
        if version_number is None:
            latest = self._session.scalar(
                select(func.max(ScenarioVersionModel.version_number)).where(
                    ScenarioVersionModel.scenario_id == scenario_id
                )
            )
            version_number = (latest or 0) + 1
        if version_number < 1:
            raise ValueError("version_number must be positive")
        version = ScenarioVersionModel(
            scenario_id=scenario_id,
            version_number=version_number,
            state_snapshot=_json_value(state_snapshot),
            scenario_snapshot=_json_value(scenario_snapshot),
        )
        self._session.add(version)
        self._session.flush()
        return to_record(version)

    def get_version(
        self, user_id: UUID, scenario_id: UUID, version_id: UUID
    ) -> dict[str, Any] | None:
        self._require_user(user_id)
        version = self._session.scalar(
            select(ScenarioVersionModel)
            .join(ScenarioModel, ScenarioModel.id == ScenarioVersionModel.scenario_id)
            .where(
                ScenarioVersionModel.id == version_id,
                ScenarioVersionModel.scenario_id == scenario_id,
                ScenarioModel.user_id == user_id,
            )
        )
        return to_record(version) if version is not None else None

    def create_branch(
        self,
        user_id: UUID,
        scenario_id: UUID,
        scenario_version_id: UUID,
        name: str,
        deltas: dict[str, Any],
        *,
        parent_branch_id: UUID | None = None,
    ) -> dict[str, Any]:
        self._require_user(user_id)
        if self.get(user_id, scenario_id) is None:
            raise ValueError("scenario does not belong to user")
        if self.get_version(user_id, scenario_id, scenario_version_id) is None:
            raise ValueError("scenario version does not belong to scenario")
        if parent_branch_id is not None:
            parent = self._session.scalar(
                select(ScenarioBranchModel)
                .join(ScenarioModel, ScenarioModel.id == ScenarioBranchModel.scenario_id)
                .where(
                    ScenarioBranchModel.id == parent_branch_id,
                    ScenarioBranchModel.scenario_id == scenario_id,
                    ScenarioModel.user_id == user_id,
                )
            )
            if parent is None:
                raise ValueError("parent branch does not belong to scenario")
        branch = ScenarioBranchModel(
            scenario_id=scenario_id,
            scenario_version_id=scenario_version_id,
            parent_branch_id=parent_branch_id,
            name=name,
            deltas=_json_value(deltas),
        )
        self._session.add(branch)
        self._session.flush()
        return to_record(branch)

    def list_branches(self, user_id: UUID, scenario_id: UUID) -> list[dict[str, Any]]:
        self._require_user(user_id)
        branches = self._session.scalars(
            select(ScenarioBranchModel)
            .join(ScenarioModel, ScenarioModel.id == ScenarioBranchModel.scenario_id)
            .where(
                ScenarioBranchModel.scenario_id == scenario_id,
                ScenarioModel.user_id == user_id,
            )
            .order_by(ScenarioBranchModel.created_at)
        )
        return [to_record(branch) for branch in branches]