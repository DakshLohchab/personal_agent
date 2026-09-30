"""Deterministic one-at-a-time sensitivity analysis."""

from collections.abc import Mapping
from decimal import Decimal

from packages.schemas.life_state import LifeState
from packages.schemas.scenario import Scenario
from packages.schemas.simulation import SensitivityResult

from .engine import simulate
from .parameters import parameter_value, set_parameter


def sensitivity_analysis(
    state: LifeState,
    scenario: Scenario,
    variable_keys: list[str],
    perturbation_percent: Decimal = Decimal(10),
    *,
    scenario_catalog: Mapping[str, Scenario] | None = None,
) -> list[SensitivityResult]:
    if perturbation_percent < 0:
        raise ValueError("perturbation_percent must be non-negative")
    baseline = simulate(
        state, scenario, enable_uncertainty=False, scenario_catalog=scenario_catalog
    ).metrics.ending_cash
    results: list[SensitivityResult] = []
    ratio = perturbation_percent / Decimal(100)
    for variable_key in variable_keys:
        current = parameter_value(state, scenario, variable_key, scenario_catalog)
        low_state, low_scenario = set_parameter(
            state, scenario, variable_key, current * (Decimal(1) - ratio), scenario_catalog
        )
        high_state, high_scenario = set_parameter(
            state, scenario, variable_key, current * (Decimal(1) + ratio), scenario_catalog
        )
        low = simulate(
            low_state,
            low_scenario,
            enable_uncertainty=False,
            scenario_catalog=scenario_catalog,
        ).metrics.ending_cash
        high = simulate(
            high_state,
            high_scenario,
            enable_uncertainty=False,
            scenario_catalog=scenario_catalog,
        ).metrics.ending_cash
        results.append(
            SensitivityResult(
                variable_key=variable_key,
                baseline_ending_cash=baseline,
                low_ending_cash=low,
                high_ending_cash=high,
                absolute_impact=max(abs(low - baseline), abs(high - baseline)),
            )
        )
    return sorted(results, key=lambda item: item.absolute_impact, reverse=True)