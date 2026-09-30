"""Bounded constraint transition search."""

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation

from packages.schemas.common import BreakpointSearchError
from packages.schemas.life_state import LifeState
from packages.schemas.scenario import Scenario

from .engine import simulate
from .parameters import set_parameter

GRID_SEARCH_STEPS = 1000


def _is_satisfied(
    state: LifeState,
    scenario: Scenario,
    constraint_id: str,
    scenario_catalog: Mapping[str, Scenario] | None,
) -> bool:
    result = simulate(
        state, scenario, enable_uncertainty=False, scenario_catalog=scenario_catalog
    )
    return not any(
        violation.constraint_id == constraint_id for violation in result.constraint_violations
    )


def _monotonic_direction(variable_key: str, metric: str) -> int | None:
    if metric == "minimum_cash":
        if variable_key in {"cash", "monthly_income"}:
            return 1
        if variable_key == "monthly_essential_expenses":
            return -1
    if metric == "maximum_monthly_spend" and variable_key == "monthly_essential_expenses":
        return -1
    if metric == "minimum_time_available" and variable_key == "monthly_time_available_hours":
        return 1
    return None


def find_breakpoint(
    state: LifeState,
    scenario: Scenario,
    variable_key: str,
    lower_bound: Decimal,
    upper_bound: Decimal,
    target_constraint_id: str,
    *,
    tolerance: Decimal = Decimal(1),
    scenario_catalog: Mapping[str, Scenario] | None = None,
) -> Decimal | None:
    if lower_bound > upper_bound:
        raise BreakpointSearchError("lower_bound must not exceed upper_bound")
    if tolerance <= 0:
        raise BreakpointSearchError("tolerance must be positive")
    constraint = next(
        (item for item in state.constraints if item.id == target_constraint_id), None
    )
    if constraint is None:
        raise BreakpointSearchError(f"unknown constraint id: {target_constraint_id}")
    try:
        set_parameter(state, scenario, variable_key, lower_bound, scenario_catalog)
        set_parameter(state, scenario, variable_key, upper_bound, scenario_catalog)
    except (ValueError, InvalidOperation) as error:
        raise BreakpointSearchError(str(error)) from error

    def satisfied_at(value: Decimal) -> bool:
        varied_state, varied_scenario = set_parameter(
            state, scenario, variable_key, value, scenario_catalog
        )
        return _is_satisfied(
            varied_state, varied_scenario, target_constraint_id, scenario_catalog
        )

    lower_satisfied = satisfied_at(lower_bound)
    upper_satisfied = satisfied_at(upper_bound)
    if lower_satisfied == upper_satisfied:
        if _monotonic_direction(variable_key, constraint.metric) is not None:
            return None
        previous_value = lower_bound
        previous_satisfied = lower_satisfied
        step = (upper_bound - lower_bound) / Decimal(GRID_SEARCH_STEPS)
        for index in range(1, GRID_SEARCH_STEPS + 1):
            value = lower_bound + step * index
            current_satisfied = satisfied_at(value)
            if current_satisfied != previous_satisfied:
                return (previous_value + value) / Decimal(2)
            previous_value = value
            previous_satisfied = current_satisfied
        return None

    direction = _monotonic_direction(variable_key, constraint.metric)
    if direction is None:
        previous_value = lower_bound
        previous_satisfied = lower_satisfied
        step = (upper_bound - lower_bound) / Decimal(GRID_SEARCH_STEPS)
        for index in range(1, GRID_SEARCH_STEPS + 1):
            value = lower_bound + step * index
            current_satisfied = satisfied_at(value)
            if current_satisfied != previous_satisfied:
                return (previous_value + value) / Decimal(2)
            previous_value = value
            previous_satisfied = current_satisfied
        return None

    left = lower_bound
    right = upper_bound
    left_satisfied = lower_satisfied
    while right - left > tolerance:
        midpoint = (left + right) / Decimal(2)
        midpoint_satisfied = satisfied_at(midpoint)
        if midpoint_satisfied == left_satisfied:
            left = midpoint
        else:
            right = midpoint
    return left if left_satisfied else right