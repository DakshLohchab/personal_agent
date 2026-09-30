"""Shared, validated handling for analysis input variations."""

from collections.abc import Mapping
from decimal import Decimal

from packages.schemas.common import InvalidScenarioError
from packages.schemas.life_state import LifeState
from packages.schemas.scenario import Scenario

from .engine import STATE_DELTA_KEYS, compose_scenario


def set_parameter(
    state: LifeState,
    scenario: Scenario,
    variable_key: str,
    value: Decimal,
    scenario_catalog: Mapping[str, Scenario] | None = None,
) -> tuple[LifeState, Scenario]:
    effective = compose_scenario(scenario, scenario_catalog)
    if variable_key in effective.deltas:
        local_deltas = dict(scenario.deltas)
        current_local = local_deltas.get(variable_key, Decimal(0))
        current_total = effective.deltas[variable_key]
        local_deltas[variable_key] = current_local + value - current_total
        return state, scenario.model_copy(update={"deltas": local_deltas})
    if variable_key in STATE_DELTA_KEYS:
        data = state.model_dump()
        data[variable_key] = value
        return LifeState.model_validate(data), scenario
    variables = list(state.variables)
    for index, variable in enumerate(variables):
        if variable.key == variable_key:
            variables[index] = variable.model_copy(update={"value": value})
            data = state.model_dump()
            data["variables"] = [item.model_dump() for item in variables]
            return LifeState.model_validate(data), scenario
    raise InvalidScenarioError(f"unknown variable key: {variable_key}")


def parameter_value(
    state: LifeState,
    scenario: Scenario,
    variable_key: str,
    scenario_catalog: Mapping[str, Scenario] | None = None,
) -> Decimal:
    effective = compose_scenario(scenario, scenario_catalog)
    if variable_key in effective.deltas:
        return effective.deltas[variable_key]
    if variable_key in STATE_DELTA_KEYS:
        return getattr(state, variable_key)
    for variable in state.variables:
        if variable.key == variable_key:
            return variable.value
    raise InvalidScenarioError(f"unknown variable key: {variable_key}")