"""User-owned structured memory operations and semantic retrieval."""

from __future__ import annotations

from typing import Any
from uuid import UUID


class MemoryService:
    def __init__(self, memory_repository: Any, embedding_repository: Any | None = None) -> None:
        self.repository = memory_repository
        self.embedding_repository = embedding_repository

    def create_memory(self, user_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
        return self.repository.create(user_id, values)

    def get_memory(self, user_id: UUID, memory_id: UUID) -> dict[str, Any] | None:
        return self.repository.get(user_id, memory_id)

    def list_memories(self, user_id: UUID) -> list[dict[str, Any]]:
        return self.repository.list_for_user(user_id)

    def update_memory(
        self, user_id: UUID, memory_id: UUID, values: dict[str, Any]
    ) -> dict[str, Any] | None:
        return self.repository.update(user_id, memory_id, values)

    def archive_memory(self, user_id: UUID, memory_id: UUID) -> dict[str, Any] | None:
        return self.update_memory(user_id, memory_id, {"status": "archived"})

    def delete_memory(self, user_id: UUID, memory_id: UUID) -> bool:
        return self.repository.delete(user_id, memory_id)

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
