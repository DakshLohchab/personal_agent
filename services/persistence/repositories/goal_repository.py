"""User-scoped goal persistence."""

from services.persistence.models import GoalModel
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository


class SqlAlchemyGoalRepository(UserOwnedSqlAlchemyRepository):
    model = GoalModel