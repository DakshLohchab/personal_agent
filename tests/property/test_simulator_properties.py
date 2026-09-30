from datetime import date
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from packages.schemas import LifeState, Scenario, Variable
from services.simulator.engine import simulate


def make_state(
    *, cash: int = 1000, income: int = 100, expenses: int = 50, horizon: int = 3
) -> LifeState:
    return LifeState(
        start_date=date(2026, 1, 1),
        horizon_months=horizon,
        cash=Decimal(cash),
        monthly_income=Decimal(income),
        monthly_essential_expenses=Decimal(expenses),
        monthly_time_available_hours=Decimal(40),
    )


@given(
    cash=st.integers(min_value=0, max_value=1_000_000),
    income=st.integers(min_value=0, max_value=10_000),
    expenses=st.integers(min_value=0, max_value=10_000),
    increase=st.integers(min_value=0, max_value=10_000),
)
def test_higher_expenses_cannot_increase_final_cash(
    cash: int, income: int, expenses: int, increase: int
) -> None:
    state = make_state(cash=cash, income=income, expenses=expenses)
    base = simulate(state, Scenario(id="base", name="Base"), enable_uncertainty=False)
    higher = simulate(
        state,
        Scenario(
            id="higher-expenses",
            name="Higher expenses",
            deltas={"monthly_essential_expenses": Decimal(increase)},
        ),
        enable_uncertainty=False,
    )
    assert higher.metrics.ending_cash <= base.metrics.ending_cash


@given(
    cash=st.integers(min_value=0, max_value=1_000_000),
    income=st.integers(min_value=0, max_value=10_000),
    increase=st.integers(min_value=0, max_value=10_000),
)
def test_higher_income_cannot_decrease_final_cash(cash: int, income: int, increase: int) -> None:
    state = make_state(cash=cash, income=income)
    base = simulate(state, Scenario(id="base", name="Base"), enable_uncertainty=False)
    higher = simulate(
        state,
        Scenario(
            id="higher-income",
            name="Higher income",
            deltas={"monthly_income": Decimal(increase)},
        ),
        enable_uncertainty=False,
    )
    assert higher.metrics.ending_cash >= base.metrics.ending_cash


@given(expense=st.integers(min_value=0, max_value=1_000_000))
def test_positive_one_time_expense_cannot_increase_final_cash(expense: int) -> None:
    state = make_state()
    base = simulate(state, Scenario(id="base", name="Base"), enable_uncertainty=False)
    purchase = simulate(
        state,
        Scenario(id="purchase", name="Purchase", deltas={"cash": Decimal(-expense)}),
        enable_uncertainty=False,
    )
    assert purchase.metrics.ending_cash <= base.metrics.ending_cash


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
@settings(max_examples=20)
def test_identical_inputs_and_seed_return_identical_results(seed: int) -> None:
    state = make_state()
    scenario = Scenario(id="base", name="Base")
    first = simulate(state, scenario, seed=seed, monte_carlo_samples=20)
    second = simulate(state, scenario, seed=seed, monte_carlo_samples=20)
    assert first == second


@given(horizon=st.integers(min_value=1, max_value=120))
def test_monthly_cash_rolls_forward_exactly(horizon: int) -> None:
    result = simulate(
        make_state(horizon=horizon), Scenario(id="base", name="Base"), enable_uncertainty=False
    )
    for previous, current in zip(result.monthly_states, result.monthly_states[1:]):
        assert current.starting_cash == previous.ending_cash


@given(
    parent_delta=st.integers(min_value=-100_000, max_value=100_000),
    child_delta=st.integers(min_value=-100_000, max_value=100_000),
)
def test_child_scenario_composes_parent_and_child_deltas(
    parent_delta: int, child_delta: int
) -> None:
    state = make_state(horizon=1)
    parent = Scenario(
        id="parent", name="Parent", deltas={"cash": Decimal(parent_delta)}
    )
    child = Scenario(
        id="child",
        name="Child",
        parent_id="parent",
        deltas={"cash": Decimal(child_delta)},
    )
    result = simulate(
        state,
        child,
        enable_uncertainty=False,
        scenario_catalog={parent.id: parent},
    )
    assert result.metrics.ending_cash == (
        state.cash
        + state.monthly_income
        - state.monthly_essential_expenses
        + Decimal(parent_delta)
        + Decimal(child_delta)
    )


@given(time=st.integers(min_value=0, max_value=40))
def test_variable_samples_respect_seed_and_are_ordered(time: int) -> None:
    state = make_state().model_copy(
        update={
            "variables": [
                Variable(
                    key="monthly_time_available_hours",
                    value=Decimal(time),
                    unit="hours",
                    min_value=Decimal(0),
                    max_value=Decimal(40),
                )
            ]
        }
    )
    result = simulate(
        state,
        Scenario(id="base", name="Base"),
        seed=91,
        monte_carlo_samples=10,
    )
    assert result.uncertainty is not None
    assert result.uncertainty.total_time_used.p05 == Decimal("0.0")