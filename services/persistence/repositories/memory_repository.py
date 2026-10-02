"""User-scoped memory persistence; files are intentionally separate records."""

from services.persistence.models import MemoryModel
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository


class SqlAlchemyMemoryRepository(UserOwnedSqlAlchemyRepository):
    model = MemoryModel