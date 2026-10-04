"""Persistence adapter for concise, user-scoped agent metadata."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from packages.schemas.agents import OrchestratedRunResult


def persist_agent_metadata(
    repository: Any,
    user_id: UUID,
    result: OrchestratedRunResult,
) -> list[dict[str, Any]]:
    """Persist final structured metadata through the existing repository boundary."""
    records: list[dict[str, Any]] = []
    for metadata in result.metadata:
        payload = metadata.model_dump(mode="json")
        payload.update(
            {
                "run_id": result.run_id,
                "output_snapshot": result.specialist_results[
                    metadata.agent_name
                ].model_dump(mode="json"),
            }
        )
        records.append(repository.create(user_id, payload))
    return records
