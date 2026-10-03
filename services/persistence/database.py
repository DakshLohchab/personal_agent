"""Central PostgreSQL engine, session factory, and transaction-scoped unit of work."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from packages.ports.auth import AuthPrincipal

load_dotenv()


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    database_url: str | None
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    echo: bool = False

    @classmethod
    def from_env(cls) -> DatabaseSettings:
        return cls(
            database_url=os.getenv("DATABASE_URL") or None,
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            echo=os.getenv("DB_ECHO", "false").strip().lower() in {"1", "true", "yes"},
        )


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgres://")
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    if database_url.startswith("postgresql+psycopg2://"):
        raise ValueError("Use the psycopg 3 driver: postgresql+psycopg://")
    if not database_url.startswith("postgresql+psycopg://"):
        raise ValueError("DATABASE_URL must use PostgreSQL with the psycopg 3 driver")
    return database_url


def create_database_engine(
    database_url: str | None = None,
    *,
    settings: DatabaseSettings | None = None,
) -> Engine:
    configuration = settings or DatabaseSettings.from_env()
    resolved_url = database_url or configuration.database_url
    if resolved_url is None:
        raise RuntimeError("DATABASE_URL must be set before opening a database connection")
    if configuration.pool_size < 1 or configuration.max_overflow < 0:
        raise ValueError("database pool size must be positive and overflow non-negative")
    if configuration.pool_timeout < 1:
        raise ValueError("DB_POOL_TIMEOUT must be positive")
    return create_engine(
        normalize_database_url(resolved_url),
        pool_pre_ping=True,
        pool_size=configuration.pool_size,
        max_overflow=configuration.max_overflow,
        pool_timeout=configuration.pool_timeout,
        echo=configuration.echo,
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_database_engine()


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False, autoflush=False)


class SqlAlchemyUnitOfWork:
    """Owns one transaction and binds PostgreSQL RLS context to that transaction."""

    def __init__(
        self,
        principal: AuthPrincipal,
        *,
        session_factory: sessionmaker[Session] | None = None,
    ) -> None:
        self.principal = principal
        factory = session_factory or get_session_factory()
        self._session = factory()
        self._transaction: Any = None

        from services.persistence.repositories.assumption_repository import (
            SqlAlchemyAssumptionRepository,
        )
        from services.persistence.repositories.commitment_repository import (
            SqlAlchemyCommitmentRepository,
        )
        from services.persistence.repositories.constraint_repository import (
            SqlAlchemyConstraintRepository,
        )
        from services.persistence.repositories.document_repository import (
            SqlAlchemyDocumentRepository,
        )
        from services.persistence.repositories.embedding_repository import (
            SqlAlchemyEmbeddingRepository,
        )
        from services.persistence.repositories.evidence_repository import (
            SqlAlchemyEvidenceRepository,
        )
        from services.persistence.repositories.file_repository import SqlAlchemyFileRepository
        from services.persistence.repositories.goal_repository import SqlAlchemyGoalRepository
        from services.persistence.repositories.memory_repository import (
            SqlAlchemyMemoryRepository,
        )
        from services.persistence.repositories.profile_repository import (
            SqlAlchemyProfileRepository,
        )
        from services.persistence.repositories.research_repository import (
            SqlAlchemyResearchRepository,
        )
        from services.persistence.repositories.run_repository import SqlAlchemyRunRepository
        from services.persistence.repositories.scenario_repository import (
            SqlAlchemyScenarioRepository,
        )

        repositories = (self._session, self.principal.user_id)
        self.profiles = SqlAlchemyProfileRepository(*repositories)
        self.goals = SqlAlchemyGoalRepository(*repositories)
        self.constraints = SqlAlchemyConstraintRepository(*repositories)
        self.commitments = SqlAlchemyCommitmentRepository(*repositories)
        self.scenarios = SqlAlchemyScenarioRepository(*repositories)
        self.assumptions = SqlAlchemyAssumptionRepository(*repositories)
        self.research = SqlAlchemyResearchRepository(*repositories)
        self.evidence = SqlAlchemyEvidenceRepository(*repositories)
        self.runs = SqlAlchemyRunRepository(*repositories)
        self.memories = SqlAlchemyMemoryRepository(*repositories)
        self.files = SqlAlchemyFileRepository(*repositories)
        self.documents = SqlAlchemyDocumentRepository(*repositories)
        self.embeddings = SqlAlchemyEmbeddingRepository(*repositories)

    def begin(self) -> None:
        if self._transaction is not None:
            raise RuntimeError("unit of work transaction is already active")
        self._transaction = self._session.begin()
        try:
            self._session.execute(
                text("SELECT set_config('app.user_id', :user_id, true)"),
                {"user_id": str(self.principal.user_id)},
            )
        except Exception:
            self._transaction.rollback()
            self._transaction = None
            raise
        self._session.info["app_user_id"] = str(self.principal.user_id)

    def commit(self) -> None:
        if self._transaction is None:
            raise RuntimeError("unit of work transaction is not active")
        self._transaction.commit()
        self._transaction = None
        self._session.info.pop("app_user_id", None)

    def rollback(self) -> None:
        if self._transaction is not None:
            self._transaction.rollback()
            self._transaction = None
        self._session.info.pop("app_user_id", None)

    def close(self) -> None:
        self.rollback()
        self._session.close()

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self.begin()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self._session.close()


def reset_database_caches() -> None:
    """Clear cached connection factories, primarily for isolated tests."""
    get_session_factory.cache_clear()
    cache_info = get_engine.cache_info()
    if cache_info.currsize:
        get_engine().dispose()
    get_engine.cache_clear()