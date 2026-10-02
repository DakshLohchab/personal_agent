"""User-scoped commitment persistence."""

from services.persistence.models import CommitmentModel
from services.persistence.repositories.base import UserOwnedSqlAlchemyRepository


class SqlAlchemyCommitmentRepository(UserOwnedSqlAlchemyRepository):
    model = CommitmentModel