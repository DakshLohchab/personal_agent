"""Controlled, provenance-aware personal memory application service."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from packages.schemas.agents import DecisionMemory, MemoryProvenance

LOGGER = logging.getLogger("life_sandbox.memory")
MEMORY_TYPES = {
    "preference",
    "stable_constraint",
    "goal",
    "commitment",
    "past_decision",
    "correction",
    "workflow_pattern",
}
MEMORY_STATUSES = {"candidate", "active", "superseded", "expired", "deleted"}
PROVENANCE_TYPES = {
    "user_confirmed",
    "user_input",
    "prior_decision",
    "system_derived",
    "imported_source",
}
SENSITIVE_PATTERN = re.compile(
    r"\b(password|passcode|secret|api[_ -]?key|token|bank account|cvv|private key)\b",
    re.IGNORECASE,
)


class MemoryPolicyError(ValueError):
    """Raised when a memory violates the controlled-memory policy."""


class MemoryService:
    def __init__(self, memory_repository: Any, embedding_repository: Any | None = None) -> None:
        self.repository = memory_repository
        self.embedding_repository = embedding_repository

    def create_memory(self, user_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
        payload = self._validate_payload(values)
        payload.setdefault("status", "candidate")
        result = self.repository.create(user_id, payload)
        LOGGER.info(
            "memory created",
            extra={
                "operation": "create",
                "user_id": str(user_id),
                "memory_type": payload["memory_type"],
            },
        )
        return result

    def get_memory(self, user_id: UUID, memory_id: UUID) -> dict[str, Any] | None:
        return self.repository.get(user_id, memory_id)

    def list_memories(self, user_id: UUID) -> list[dict[str, Any]]:
        return self.repository.list_for_user(user_id)

    def update_memory(
        self, user_id: UUID, memory_id: UUID, values: dict[str, Any]
    ) -> dict[str, Any] | None:
        payload = self._validate_payload(values, partial=True)
        payload.pop("status", None)
        return self.repository.update(user_id, memory_id, payload)

    def approve_memory(self, user_id: UUID, memory_id: UUID) -> dict[str, Any] | None:
        result = self.repository.approve(user_id, memory_id)
        LOGGER.info(
            "memory approval completed",
            extra={"operation": "approve", "user_id": str(user_id), "result": result is not None},
        )
        return result

    def delete_memory(self, user_id: UUID, memory_id: UUID) -> bool:
        return self.repository.forget(user_id, memory_id)

    def search_memories(
        self, user_id: UUID, query_embedding: list[float], model_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        if self.embedding_repository is None:
            raise RuntimeError("embedding repository is required for semantic search")
        return self.embedding_repository.search_memories(
            user_id, query_embedding, model_name=model_name, limit=limit
        )

    def search_evidence(
        self, user_id: UUID, query_embedding: list[float], model_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        if self.embedding_repository is None:
            raise RuntimeError("embedding repository is required for semantic search")
        return self.embedding_repository.search_evidence(
            user_id, query_embedding, model_name=model_name, limit=limit
        )

    def retrieve_relevant_memories(
        self,
        user_id: UUID,
        decision_context: str | dict[str, Any],
        *,
        filters: set[str] | None = None,
        limit: int = 10,
        query_embedding: list[float] | None = None,
        model_name: str | None = None,
    ) -> list[DecisionMemory]:
        if limit < 1 or limit > 50:
            raise ValueError("limit must be between 1 and 50")
        records = self.repository.list_valid(user_id, filters)
        records = [record for record in records if self._not_expired(record)]
        context_text = self._context_text(decision_context)
        context_tokens = set(re.findall(r"[a-z0-9_]+", context_text.lower()))
        current_keys = set(decision_context) if isinstance(decision_context, dict) else set()
        records = [
            record
            for record in records
            if not current_keys.intersection(record.get("structured_data", {}).keys())
        ]
        semantic_ids: dict[UUID, float] = {}
        if query_embedding is not None and model_name and self.embedding_repository is not None:
            for record in self.embedding_repository.search_memories(
                user_id, query_embedding, model_name=model_name, limit=limit
            ):
                if record.get("status") == "active" and self._not_expired(record):
                    semantic_ids[record["id"]] = 1 - float(record.get("cosine_distance", 1))
        ranked = sorted(
            records,
            key=lambda record: (
                len(
                    context_tokens.intersection(
                        set(re.findall(r"[a-z0-9_]+", str(record["content"]).lower()))
                    )
                ),
                semantic_ids.get(record["id"], 0.0),
                record.get("last_confirmed_at") or record.get("updated_at"),
                str(record["id"]),
            ),
            reverse=True,
        )
        result = [
            self._to_decision_memory(record, context_tokens, semantic_ids)
            for record in ranked[:limit]
        ]
        LOGGER.info(
            "memory retrieval completed",
            extra={
                "operation": "retrieve",
                "user_id": str(user_id),
                "retrieval_method": "structured+semantic" if semantic_ids else "structured",
                "count": len(result),
            },
        )
        return result

    @staticmethod
    def _not_expired(record: dict[str, Any]) -> bool:
        expires_at = record.get("expires_at")
        return expires_at is None or expires_at > datetime.now(timezone.utc)

    @staticmethod
    def _context_text(context: str | dict[str, Any]) -> str:
        return (
            context
            if isinstance(context, str)
            else " ".join(f"{key} {value}" for key, value in context.items())
        )

    @staticmethod
    def _to_decision_memory(
        record: dict[str, Any], context_tokens: set[str], semantic_ids: dict[UUID, float]
    ) -> DecisionMemory:
        provenance_type = record.get("provenance_type") or "user_input"
        labels = {
            "user_confirmed": "Previously confirmed by you",
            "user_input": "Provided in your input",
            "prior_decision": "From a prior decision",
            "system_derived": "Derived by the system",
            "imported_source": "Imported source",
        }
        overlap = len(
            context_tokens.intersection(
                set(re.findall(r"[a-z0-9_]+", str(record["content"]).lower()))
            )
        )
        reason = "Matched this decision context" if overlap else "Relevant saved context"
        if semantic_ids.get(record["id"], 0) > 0:
            reason = "Semantically relevant to this decision"
        return DecisionMemory(
            memory_id=record["id"],
            memory_type=record["memory_type"],
            content=record["content"],
            confidence=float(record["confidence"])
            if record.get("confidence") is not None
            else None,
            provenance=MemoryProvenance(
                type=provenance_type,
                reference=record.get("provenance_ref"),
                label=labels.get(provenance_type, provenance_type),
            ),
            retrieval_reason=reason,
            last_confirmed_at=record.get("last_confirmed_at"),
        )

    @staticmethod
    def _validate_payload(values: dict[str, Any], partial: bool = False) -> dict[str, Any]:
        payload = dict(values)
        if "memory_type" in payload and payload["memory_type"] not in MEMORY_TYPES:
            raise MemoryPolicyError("unsupported memory type")
        if "status" in payload and payload["status"] not in MEMORY_STATUSES:
            raise MemoryPolicyError("unsupported memory status")
        if "provenance_type" in payload and payload["provenance_type"] not in PROVENANCE_TYPES:
            raise MemoryPolicyError("unsupported provenance type")
        if not partial and not payload.get("content", "").strip():
            raise MemoryPolicyError("memory content is required")
        if SENSITIVE_PATTERN.search(str(payload.get("content", ""))):
            raise MemoryPolicyError("sensitive credentials cannot be stored as memory")
        if payload.get("confidence") is not None and not 0 <= payload["confidence"] <= 1:
            raise MemoryPolicyError("confidence must be between 0 and 1")
        return payload
