"""Profile repository keyed by the trusted internal auth principal."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.ports.auth import AuthPrincipal
from services.persistence.models import ProfileModel
from services.persistence.repositories.base import require_user_transaction, to_record


class SqlAlchemyProfileRepository:
    def __init__(self, session: Session, user_id: UUID) -> None:
        self._session = session
        self._user_id = user_id

    def create(
        self,
        principal: AuthPrincipal,
        *,
        display_name: str | None = None,
        timezone: str | None = None,
    ) -> dict[str, object]:
        require_user_transaction(self._session, principal.user_id, self._user_id)
        profile = ProfileModel(
            id=principal.user_id,
            auth_subject=principal.auth_subject,
            auth_provider=principal.provider,
            display_name=display_name,
            timezone=timezone,
        )
        self._session.add(profile)
        self._session.flush()
        return to_record(profile)

    def get(self, user_id: UUID) -> dict[str, object] | None:
        self._require_user(user_id)
        profile = self._session.scalar(select(ProfileModel).where(ProfileModel.id == user_id))
        return to_record(profile) if profile is not None else None

    def delete(self, user_id: UUID) -> bool:
        self._require_user(user_id)
        profile = self._session.scalar(select(ProfileModel).where(ProfileModel.id == user_id))
        if profile is None:
            return False
        self._session.delete(profile)
        self._session.flush()
        return True

    def _require_user(self, user_id: UUID) -> None:
        require_user_transaction(self._session, user_id, self._user_id)