from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from packages.schemas import Commitment, Goal, LifeState, Variable
from tests.fixtures.golden_cases import base_state


def test_rejects_negative_state_money() -> None:
    with pytest.raises(ValidationError):
        base_state(cash=Decimal(-1))


def test_rejects_float_money() -> None:
    with pytest.raises(ValidationError):
        base_state(monthly_income=1.25)


def test_rejects_invalid_horizon_and_datetime() -> None:
    with pytest.raises(ValidationError):
        base_state(horizon_months=121)
    with pytest.raises(ValidationError):
        LifeState(
            start_date=datetime(2026, 1, 1),
            horizon_months=1,
            cash=Decimal(1),
            monthly_income=Decimal(1),
            monthly_essential_expenses=Decimal(1),
            monthly_time_available_hours=Decimal(1),
        )


def test_accepts_date_and_decimal_values() -> None:
    state = base_state(start_date=date(2026, 2, 3))
    assert state.cash == Decimal(50000)


def test_validates_commitments_and_variable_ranges() -> None:
    with pytest.raises(ValidationError):
        Commitment(id="bad", name="Bad", monthly_cost=Decimal(-1))
    with pytest.raises(ValidationError):
        Variable(
            key="monthly_income",
            value=Decimal(5),
            unit="currency",
            min_value=Decimal(6),
        )


def test_goal_decimal_values_reject_floats() -> None:
    with pytest.raises(ValidationError):
        Goal(id="savings", name="Savings", target_value=100.5)