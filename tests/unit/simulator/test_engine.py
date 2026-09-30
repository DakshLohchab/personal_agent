from decimal import Decimal

import pytest

from packages.schemas import Constraint, Scenario
from services.simulator.engine import compose_scenario, simulate
from tests.fixtures.golden_cases import GoldenCase, golden_cases


@pytest.mark.parametrize("case", golden_cases(), ids=lambda case: case.name)
def test_golden_scenarios(case: GoldenCase) -> None:
    result = simulate(
        case.state,
        case.scenario,
        enable_uncertainty=False,
        scenario_catalog=case.scenario_catalog,
    )
    assert tuple(item.ending_cash for item in result.monthly_states) == case.expected_monthly_cash
    assert result.metrics.ending_cash == case.expected_final_cash
    assert result.metrics.minimum_cash == case.expected_minimum_cash
    assert result.metrics.total_spend == case.expected_total_spend
    assert tuple(
        (item.month, item.constraint_id, item.observed, item.limit)
        for item in result.constraint_violations
    ) == case.expected_violations


def test_cash_delta_is_only_applied_once() -> None:
    case = golden_cases()[1]
    result = simulate(case.state, case.scenario, enable_uncertainty=False)
    assert result.monthly_states[0].one_time_adjustments == Decimal(-35000)
    assert result.monthly_states[1].one_time_adjustments == Decimal(0)


def test_one_time_purchase_counts_toward_monthly_spend_constraint() -> None:
    case = golden_cases()[0]
    state = case.state.model_copy(
        update={
            "constraints": [
                Constraint(
                    id="spend-limit",
                    name="Spend limit",
                    metric="maximum_monthly_spend",
                    limit=Decimal(40000),
                )
            ]
        }
    )
    laptop_case = golden_cases()[1]
    result = simulate(state, laptop_case.scenario, enable_uncertainty=False)
    assert [item.observed for item in result.constraint_violations] == [Decimal(47000)]


def test_negative_scenario_time_is_clamped_and_reported() -> None:
    state = golden_cases()[0].state.model_copy(
        update={
            "monthly_time_available_hours": Decimal(10),
            "constraints": [
                Constraint(
                    id="minimum-time",
                    name="Minimum time",
                    metric="minimum_time_available",
                    limit=Decimal(1),
                )
            ],
        }
    )
    scenario = Scenario(
        id="less-time",
        name="Less time",
        deltas={"monthly_time_available_hours": Decimal(-20)},
    )
    result = simulate(state, scenario, enable_uncertainty=False)
    assert all(month.time_available_hours == Decimal(0) for month in result.monthly_states)
    assert [violation.observed for violation in result.constraint_violations] == [
        Decimal(0),
        Decimal(0),
    ]


def test_scenario_branch_composes_ancestor_deltas() -> None:
    parent = Scenario(id="parent", name="Parent", deltas={"cash": Decimal(-10)})
    child = Scenario(
        id="child", name="Child", parent_id="parent", deltas={"cash": Decimal(-5)}
    )
    resolved = compose_scenario(child, {parent.id: parent})
    assert resolved.deltas == {"cash": Decimal(-15)}


def test_missing_parent_fails_loudly() -> None:
    from packages.schemas import InvalidScenarioError

    child = Scenario(id="child", name="Child", parent_id="missing")
    with pytest.raises(InvalidScenarioError):
        simulate(golden_cases()[0].state, child, enable_uncertainty=False)