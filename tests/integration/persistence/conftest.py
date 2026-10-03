from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from packages.ports.auth import AuthPrincipal
from services.persistence.database import SqlAlchemyUnitOfWork, normalize_database_url
from tests.fixtures.fake_auth import FakeAuthProvider


@dataclass(frozen=True)
class PersistenceContext:
    principal: AuthPrincipal
    session_factory: sessionmaker[Session]
    engine: Engine

    def unit_of_work(self, principal: AuthPrincipal | None = None) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(
            principal or self.principal,
            session_factory=self.session_factory,
        )


def _migration_config(database_url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option(
        "sqlalchemy.url", normalize_database_url(database_url).replace("%", "%%")
    )
    return config


@pytest.fixture(scope="session")
def postgres_engine() -> Iterator[Engine]:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set TEST_DATABASE_URL to run PostgreSQL persistence integration tests")
    if make_url(database_url).host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail(
            "TEST_DATABASE_URL must point to a local database; migration tests are destructive"
        )
    normalized_url = normalize_database_url(database_url)
    command.upgrade(_migration_config(normalized_url), "head")
    engine = create_engine(normalized_url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def user_context(postgres_engine: Engine) -> Iterator[PersistenceContext]:
    principal = AuthPrincipal(uuid4(), f"integration-{uuid4()}", "fake")
    auth_provider = FakeAuthProvider({"test-token": principal})
    authenticated = auth_provider.authenticate("test-token")
    assert authenticated == principal
    context = PersistenceContext(
        principal=principal,
        engine=postgres_engine,
        session_factory=sessionmaker(
            bind=postgres_engine,
            expire_on_commit=False,
            autoflush=False,
        ),
    )
    with context.unit_of_work() as unit_of_work:
        unit_of_work.profiles.create(principal)
    yield context
    with context.unit_of_work() as unit_of_work:
        unit_of_work.profiles.delete(principal.user_id)


__all__ = ["PersistenceContext", "postgres_engine", "user_context"]