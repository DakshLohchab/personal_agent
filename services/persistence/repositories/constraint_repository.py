"""User-scoped constraint persistence."""

from services.persistence.models import ConstraintModel
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository


class SqlAlchemyConstraintRepository(UserOwnedSqlAlchemyRepository):
    model = ConstraintModel