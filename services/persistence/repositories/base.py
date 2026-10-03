"""Shared SQLAlchemy operations with mandatory user scoping."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session


def require_user_transaction(
    session: Session, requested_user_id: UUID, owner_user_id: UUID
) -> None:
    if requested_user_id != owner_user_id:
        raise PermissionError("repository access must use the authenticated user")
    if (
        not session.in_transaction()
        or session.info.get("app_user_id") != str(owner_user_id)
    ):
        raise RuntimeError(
            "repository operation requires an authenticated unit-of-work transaction"
        )


def to_record(entity: Any) -> dict[str, Any]:
    """Return column data only; never return an ORM entity to application code."""
    return {
        attribute.key: getattr(entity, attribute.key)
        for attribute in inspect(entity).mapper.column_attrs
    }


class UserOwnedSqlAlchemyRepository:
    model: type[Any]

    def __init__(self, session: Session, user_id: UUID) -> None:
        self._session = session
        self._user_id = user_id

    def _require_user(self, user_id: UUID) -> None:
        require_user_transaction(self._session, user_id, self._user_id)

    def create(self, user_id: UUID, values: Any) -> dict[str, Any]:
        self._require_user(user_id)
        payload = dict(values)
        payload.pop("user_id", None)
        payload.pop("id", None)
        entity = self.model(user_id=user_id, **payload)
        self._session.add(entity)
        self._session.flush()
        return to_record(entity)

    def get(self, user_id: UUID, record_id: UUID) -> dict[str, Any] | None:
        self._require_user(user_id)
        entity = self._session.scalar(
            select(self.model).where(self.model.id == record_id, self.model.user_id == user_id)
        )
        return to_record(entity) if entity is not None else None

    def list_for_user(self, user_id: UUID) -> list[dict[str, Any]]:
        self._require_user(user_id)
        entities = self._session.scalars(
            select(self.model).where(self.model.user_id == user_id).order_by(self.model.created_at)
        )
        return [to_record(entity) for entity in entities]

    def update(
        self, user_id: UUID, record_id: UUID, values: Any
    ) -> dict[str, Any] | None:
        self._require_user(user_id)
        entity = self._session.scalar(
            select(self.model).where(self.model.id == record_id, self.model.user_id == user_id)
        )
        if entity is None:
            return None
        mapped_columns = inspect(self.model).columns
        for key, value in dict(values).items():
            column = mapped_columns.get(key)
            if (
                column is not None
                and not column.primary_key
                and not column.foreign_keys
                and key not in {"user_id", "created_at", "updated_at"}
            ):
                setattr(entity, key, value)
        self._session.flush()
        return to_record(entity)

    def delete(self, user_id: UUID, record_id: UUID) -> bool:
        self._require_user(user_id)
        entity = self._session.scalar(
            select(self.model).where(self.model.id == record_id, self.model.user_id == user_id)
        )
        if entity is None:
            return False
        self._session.delete(entity)
        self._session.flush()
        return True