"""User-scoped document metadata and chunk persistence."""

from hashlib import sha256
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.persistence.models import DocumentChunkModel, DocumentModel, FileModel
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository, to_record


class SqlAlchemyDocumentRepository(UserOwnedSqlAlchemyRepository):
    model = DocumentModel

    def __init__(self, session: Session, user_id: UUID) -> None:
        super().__init__(session, user_id)
        self._session = session

    def create(self, user_id: UUID, values: dict[str, Any]) -> dict[str, Any]:
        self._require_user(user_id)
        payload = dict(values)
        file_id = payload.get("file_id")
        if file_id is not None:
            file_record = self._session.scalar(
                select(FileModel).where(FileModel.id == file_id, FileModel.user_id == user_id)
            )
            if file_record is None:
                raise ValueError("file does not belong to user")
        content = payload.get("content", "")
        payload.setdefault("document_type", "unknown")
        payload.setdefault("title", payload.get("document_type", "Document"))
        payload.setdefault("content", content)
        return super().create(user_id, payload)

    def create_chunk(
        self, user_id: UUID, document_id: UUID, values: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_user(user_id)
        if self.get(user_id, document_id) is None:
            raise ValueError("document does not belong to user")
        payload = dict(values)
        text = payload.pop("text", payload.pop("content", ""))
        payload.setdefault("content", text)
        payload.setdefault("content_hash", sha256(text.encode()).hexdigest())
        chunk = DocumentChunkModel(
            user_id=user_id, document_id=document_id, text=text, **payload
        )
        self._session.add(chunk)
        self._session.flush()
        return to_record(chunk)

    def list_chunks(self, user_id: UUID, document_id: UUID) -> list[dict[str, Any]]:
        self._require_user(user_id)
        chunks = self._session.scalars(
            select(DocumentChunkModel)
            .join(DocumentModel, DocumentModel.id == DocumentChunkModel.document_id)
            .where(
                DocumentChunkModel.document_id == document_id,
                DocumentChunkModel.user_id == user_id,
                DocumentModel.user_id == user_id,
            )
            .order_by(DocumentChunkModel.chunk_index)
        )
        return [to_record(chunk) for chunk in chunks]

    def get_chunk(self, user_id: UUID, chunk_id: UUID) -> dict[str, Any] | None:
        self._require_user(user_id)
        chunk = self._session.scalar(
            select(DocumentChunkModel)
            .join(DocumentModel, DocumentModel.id == DocumentChunkModel.document_id)
            .where(
                DocumentChunkModel.id == chunk_id,
                DocumentChunkModel.user_id == user_id,
                DocumentModel.user_id == user_id,
            )
        )
        return to_record(chunk) if chunk is not None else None

    def store_chunk_embedding(
        self, user_id: UUID, chunk_id: UUID, model_name: str, embedding: list[float]
    ) -> dict[str, Any]:
        self._require_user(user_id)
        if self.get_chunk(user_id, chunk_id) is None:
            raise ValueError("document chunk does not belong to user")
        from services.persistence.repositories.embedding_repository import (
            SqlAlchemyEmbeddingRepository,
        )

        return SqlAlchemyEmbeddingRepository(self._session, self._user_id).create(
            user_id,
            {
                "document_chunk_id": chunk_id,
                "model_name": model_name,
                "dimensions": len(embedding),
                "embedding": embedding,
            },
        )