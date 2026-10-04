"""User-scoped persistence for concise agent execution metadata."""

from services.persistence.models import AgentRunModel
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository


class SqlAlchemyAgentRunRepository(UserOwnedSqlAlchemyRepository):
    model = AgentRunModel
