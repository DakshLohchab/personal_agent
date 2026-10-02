from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from packages.ports.auth import AuthPrincipal
from services.persistence.database import (
    DatabaseSettings,
    create_database_engine,
    normalize_database_url,
)
from services.persistence.models import GoalModel
from services.persistence.repositories.base import (
    UserOwnedSqlAlchemyRepository,
    to_record,
)
from tests.fixtures.fake_auth import FakeAuthProvider


def test_database_settings_have_safe_local_defaults(monkeypatch) -> None:
    for variable in (
        "DATABASE_URL",
        "DB_POOL_SIZE",
        "DB_MAX_OVERFLOW",
        "DB_POOL_TIMEOUT",
        "DB_ECHO",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = DatabaseSettings.from_env()

    assert settings.database_url is None
    assert settings.pool_size == 5
    assert settings.max_overflow == 10
    assert settings.pool_timeout == 30
    assert settings.echo is False


def test_database_url_uses_psycopg_three() -> None:
    assert normalize_database_url("postgres://user:pass@localhost/db") == (
        "postgresql+psycopg://user:pass@localhost/db"
    )
    assert normalize_database_url("postgresql://user:pass@localhost/db") == (
        "postgresql+psycopg://user:pass@localhost/db"
    )
    with pytest.raises(ValueError, match="psycopg 3"):
        normalize_database_url("postgresql+psycopg2://user:pass@localhost/db")


def test_engine_is_pooled_and_does_not_connect_until_used() -> None:
    engine = create_database_engine(
        "postgresql+psycopg://user:pass@localhost/db",
        settings=DatabaseSettings(None, pool_size=3, max_overflow=2, pool_timeout=8),
    )
    try:
        assert engine.pool.size() == 3
        assert engine.pool._max_overflow == 2
        assert engine.pool._timeout == 8
    finally:
        engine.dispose()


def test_missing_database_url_does_not_affect_simulator(monkeypatch) -> None:
    from services.simulator.engine import simulate
    from tests.fixtures.golden_cases import golden_cases

    monkeypatch.delenv("DATABASE_URL", raising=False)
    case = golden_cases()[0]

    result = simulate(case.state, case.scenario, enable_uncertainty=False)

    assert result.metrics.ending_cash == case.expected_final_cash


def test_fake_auth_provider_maps_credentials_to_internal_principals() -> None:
    principal = AuthPrincipal(uuid4(), "test-subject", "fake")
    provider = FakeAuthProvider({"valid": principal})

    assert provider.authenticate("valid") == principal
    assert provider.authenticate("unknown") is None


def test_sqlalchemy_entities_are_not_returned_from_repository_records() -> None:
    goal = GoalModel(
        id=uuid4(),
        user_id=uuid4(),
        name="Reserve",
        target_value=Decimal("250.75"),
    )

    record = to_record(goal)

    assert not isinstance(record, GoalModel)
    assert record["target_value"] == Decimal("250.75")
    sql = str(
        select(GoalModel).where(GoalModel.user_id == uuid4()).compile(
            dialect=postgresql.dialect()
        )
    )
    assert "goals.user_id = " in sql


def test_repository_requires_a_principal_bound_transaction() -> None:
    principal_id = uuid4()
    with Session(create_engine("sqlite://")) as session:
        repository = UserOwnedSqlAlchemyRepository(session, principal_id)
        with pytest.raises(RuntimeError, match="unit-of-work transaction"):
            repository.list_for_user(principal_id)