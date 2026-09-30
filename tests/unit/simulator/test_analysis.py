from decimal import Decimal

from packages.schemas import Constraint, LifeState, Scenario, Variable
from services.simulator.breakpoint import find_breakpoint
from services.simulator.sensitivity import sensitivity_analysis
from services.simulator.uncertainty import calculate_uncertainty
from tests.fixtures.golden_cases import base_state


def test_uncertainty_is_seeded_and_has_requested_sample_count() -> None:
    state = base_state(
        variables=[
            Variable(
                key="monthly_income",
                value=Decimal(20000),
                unit="currency/month",
                min_value=Decimal(10000),
                max_value=Decimal(30000),
            )
        ]
    )
    scenario = Scenario(id="base", name="Base")
    first = calculate_uncertainty(state, scenario, seed=42, sample_count=25)
    second = calculate_uncertainty(state, scenario, seed=42, sample_count=25)
    assert first == second
    assert first.sample_count == 25
    assert first.ending_cash.p05 <= first.ending_cash.p50 <= first.ending_cash.p95


def test_sensitivity_orders_larger_impacts_first() -> None:
    results = sensitivity_analysis(
        base_state(),
        Scenario(id="base", name="Base"),
        ["monthly_income", "monthly_essential_expenses"],
    )
    assert results[0].absolute_impact >= results[1].absolute_impact
    assert all(item.absolute_impact > 0 for item in results)


def test_breakpoint_finds_minimum_cash_transition() -> None:
    state = base_state(
        constraints=[
            Constraint(
                id="reserve",
                name="Reserve",
                metric="minimum_cash",
                limit=Decimal(60000),
            )
        ]
    )
    breakpoint = find_breakpoint(
        state,
        Scenario(id="base", name="Base"),
        "cash",
        Decimal(50000),
        Decimal(60000),
        "reserve",
        tolerance=Decimal(1),
    )
    assert breakpoint is not None
    assert Decimal(52000) <= breakpoint <= Decimal(52001)


def test_grid_search_returns_none_for_unchanging_extension_variable() -> None:
    state: LifeState = base_state(
        constraints=[
            Constraint(
                id="reserve",
                name="Reserve",
                metric="minimum_cash",
                limit=Decimal(1),
            )
        ],
        variables=[Variable(key="laptop_cost", value=Decimal(100), unit="currency")],
    )
    assert (
        find_breakpoint(
            state,
            Scenario(id="base", name="Base"),
            "laptop_cost",
            Decimal(0),
            Decimal(200),
            "reserve",
        )
        is None
    )