"""Provider-neutral vector storage contract."""

from typing import Any, Protocol
from uuid import UUID


class VectorStore(Protocol):
    def upsert_embedding(
        self, user_id: UUID, owner: dict[str, UUID], model_name: str, embedding: list[float]
    ) -> dict[str, Any]: ...

    def search_similar(
        self, user_id: UUID, query_embedding: list[float], model_name: str, limit: int = 10
    ) -> list[dict[str, Any]]: ...

    def delete_embedding(self, user_id: UUID, embedding_id: UUID) -> bool: ...

