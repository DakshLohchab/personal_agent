"""User-scoped file metadata persistence; no binary file store is included."""

from services.persistence.models import FileModel
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository


class SqlAlchemyFileRepository(UserOwnedSqlAlchemyRepository):
    model = FileModel