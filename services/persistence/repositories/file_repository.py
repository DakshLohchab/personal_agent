"""User-scoped file metadata persistence; binary data stays in object storage."""

from uuid import uuid4

from services.persistence.models import FileModel
from services.persistence.repositories.base import (
    UserOwnedSqlAlchemyRepository,
    to_record,
)


class SqlAlchemyFileRepository(UserOwnedSqlAlchemyRepository):
    model = FileModel

    def create(self, user_id, values):
        payload = dict(values)
        filename = payload.pop("original_filename", payload.pop("original_name", "file"))
        payload.setdefault("original_name", filename)
        payload.setdefault("mime_type", payload.pop("media_type", "application/octet-stream"))
        payload.setdefault("media_type", payload["mime_type"])
        payload.setdefault("size_bytes", 0)
        payload.setdefault("object_key", f"users/{user_id}/files/{uuid4()}/{filename}")
        payload.setdefault("created_by", user_id)
        self._require_user(user_id)
        entity = FileModel(
            id=payload.pop("id", None) or uuid4(),
            user_id=user_id,
            original_filename=filename,
            **payload,
        )
        self._session.add(entity)
        self._session.flush()
        return to_record(entity)