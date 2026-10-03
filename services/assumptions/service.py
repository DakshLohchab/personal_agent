"""Assumption lifecycle with explicit provenance rules delegated to persistence."""

from typing import Any
from uuid import UUID


class AssumptionService:
    def __init__(self, repository: Any) -> None:
        self.repository = repository

    def create_assumption(self, user_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
        return self.repository.create(user_id, values)

    def update_assumption(
        self, user_id: UUID, assumption_id: UUID, values: dict[str, Any]
    ) -> dict[str, Any] | None:
        return self.repository.update(user_id, assumption_id, values)
