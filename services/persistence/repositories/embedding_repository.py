"""User-scoped embedding persistence and exact cosine-distance search."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
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

    def upsert_embedding(
        self, user_id: UUID, owner: dict[str, UUID], model_name: str, embedding: list[float]
    ) -> dict[str, Any]:
        self._require_user(user_id)
        owner_fields = {"memory_id", "document_chunk_id", "evidence_id"}
        if set(owner) - owner_fields or len(owner) != 1:
            raise ValueError("embedding must have exactly one semantic owner")
        existing = self._session.scalar(
            select(EmbeddingModel).where(
                EmbeddingModel.user_id == user_id,
                EmbeddingModel.model_name == model_name,
                *[getattr(EmbeddingModel, key) == value for key, value in owner.items()],
            )
        )
        if existing is not None:
            existing.embedding = embedding
            existing.dimensions = len(embedding)
            self._session.flush()
            return to_record(existing)
        return self.create(
            user_id,
            {
                **owner,
                "model_name": model_name,
                "dimensions": len(embedding),
                "embedding": embedding,
            },
        )

    def search_memories(
        self, user_id: UUID, vector: list[float], *, model_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        return self._semantic_search(user_id, vector, model_name, MemoryModel, limit)

    def search_evidence(
        self, user_id: UUID, vector: list[float], *, model_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        rows = self._semantic_search(user_id, vector, model_name, EvidenceModel, limit)
        return [
            {
                "evidence_id": row["evidence_id"],
                "claim": row["claim_text"],
                "evidence_text": row["evidence_text"],
                "source_url": row["source_url"],
                "similarity": 1 - float(row["cosine_distance"]),
                "retrieved_at": row["created_at"],
            }
            for row in rows
        ]

    def _semantic_search(
        self, user_id: UUID, vector: list[float], model_name: str, owner_model: Any, limit: int
    ) -> list[dict[str, Any]]:
        self._require_user(user_id)
        if not vector or limit < 1:
            raise ValueError("query vector must not be empty and limit must be positive")
        distance = EmbeddingModel.embedding.cosine_distance(vector)
        owner_id = (
            EmbeddingModel.memory_id if owner_model is MemoryModel else EmbeddingModel.evidence_id
        )
        rows = self._session.execute(
            select(EmbeddingModel, owner_model, distance.label("cosine_distance"))
            .join(owner_model, owner_model.id == owner_id)
            .where(
                EmbeddingModel.user_id == user_id,
                EmbeddingModel.model_name == model_name,
                EmbeddingModel.dimensions == len(vector),
                owner_model.user_id == user_id,
                *(
                    [
                        owner_model.status == "active",
                        owner_model.expires_at.is_(None) | (owner_model.expires_at > func.now()),
                    ]
                    if owner_model is MemoryModel
                    else []
                ),
            )
            .order_by(distance)
            .limit(limit)
        )
        return [
            {**to_record(embedding), **to_record(owner), "cosine_distance": cosine_distance}
            for embedding, owner, cosine_distance in rows
        ]

    def delete_embedding(self, user_id: UUID, embedding_id: UUID) -> bool:
        self._require_user(user_id)
        entity = self._session.scalar(
            select(EmbeddingModel).where(
                EmbeddingModel.id == embedding_id, EmbeddingModel.user_id == user_id
            )
        )
        if entity is None:
            return False
        self._session.delete(entity)
        self._session.flush()
        return True
