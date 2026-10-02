"""User-scoped embedding persistence and exact cosine-distance search."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.persistence.models import (
    DocumentChunkModel,
    EmbeddingModel,
    EvidenceModel,
    MemoryModel,
)
from services.persistence.repositories.base import require_user_transaction, to_record


class SqlAlchemyEmbeddingRepository:
    def __init__(self, session: Session, user_id: UUID) -> None:
        self._session = session
        self._user_id = user_id

    def _require_user(self, user_id: UUID) -> None:
        require_user_transaction(self._session, user_id, self._user_id)

    def create(self, user_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
        self._require_user(user_id)
        payload = dict(values)
        payload.pop("user_id", None)
        payload.pop("id", None)
        owner_fields = ["memory_id", "document_chunk_id", "evidence_id"]
        selected_owners = [field for field in owner_fields if payload.get(field) is not None]
        if len(selected_owners) != 1:
            raise ValueError("embedding must have exactly one semantic owner")
        owner_field = selected_owners[0]
        owner_id = payload[owner_field]
        owner_model = {
            "memory_id": MemoryModel,
            "document_chunk_id": DocumentChunkModel,
            "evidence_id": EvidenceModel,
        }[owner_field]
        owner = self._session.scalar(
            select(owner_model).where(
                owner_model.id == owner_id,
                owner_model.user_id == user_id,
            )
        )
        if owner is None:
            raise ValueError("embedding owner does not belong to user")
        vector = payload.get("embedding")
        dimensions = payload.get("dimensions")
        if vector is not None and len(vector) != dimensions:
            raise ValueError("embedding dimensions do not match vector length")
        entity = EmbeddingModel(user_id=user_id, **payload)
        self._session.add(entity)
        self._session.flush()
        return to_record(entity)

    def exact_cosine_search(
        self,
        user_id: UUID,
        vector: list[float],
        *,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        self._require_user(user_id)
        if not vector:
            raise ValueError("query vector must not be empty")
        if limit < 1:
            raise ValueError("limit must be positive")
        distance = EmbeddingModel.embedding.cosine_distance(vector)
        rows = self._session.execute(
            select(EmbeddingModel, distance.label("cosine_distance"))
            .where(
                EmbeddingModel.user_id == user_id,
                EmbeddingModel.embedding.is_not(None),
                EmbeddingModel.dimensions == len(vector),
            )
            .order_by(distance)
            .limit(limit)
        )
        return [
            {**to_record(entity), "cosine_distance": cosine_distance}
            for entity, cosine_distance in rows
        ]