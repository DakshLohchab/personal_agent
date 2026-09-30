"""Seeded Monte Carlo sampling, kept outside the monthly calculation."""

from collections.abc import Mapping
from decimal import Decimal

import numpy as np

from packages.schemas.life_state import LifeState
from packages.schemas.scenario import Scenario
from packages.schemas.simulation import PercentileMetrics, UncertaintyResult

from .engine import STATE_DELTA_KEYS, simulate


def _sample_state(state: LifeState, generator: np.random.Generator) -> LifeState:
    data = state.model_dump()
    for index, variable in enumerate(state.variables):
        if variable.min_value is None or variable.max_value is None:
            continue
        sample = Decimal(
            str(generator.uniform(float(variable.min_value), float(variable.max_value)))
        )
        if variable.key in STATE_DELTA_KEYS:
            data[variable.key] = sample
        data["variables"][index]["value"] = sample
    return LifeState.model_validate(data)


def _percentiles(values: list[Decimal]) -> PercentileMetrics:
    percentile_values = np.percentile(np.asarray([float(value) for value in values]), [5, 50, 95])
    return PercentileMetrics(
        p05=Decimal(str(percentile_values[0])),
        p50=Decimal(str(percentile_values[1])),
        p95=Decimal(str(percentile_values[2])),
    )


def calculate_uncertainty(
    state: LifeState,
    scenario: Scenario,
    *,
    seed: int,
    sample_count: int,
    scenario_catalog: Mapping[str, Scenario] | None = None,
) -> UncertaintyResult:
    """Sample ranged variables, then run the deterministic engine per sample."""
    if sample_count < 1:
        raise ValueError("sample_count must be positive")
    generator = np.random.default_rng(seed)
    sampled_results = [
        simulate(
            _sample_state(state, generator),
            scenario,
            seed=seed,
            enable_uncertainty=False,
            scenario_catalog=scenario_catalog,
        )
        for _ in range(sample_count)
    ]
    return UncertaintyResult(
        ending_cash=_percentiles([item.metrics.ending_cash for item in sampled_results]),
        minimum_cash=_percentiles([item.metrics.minimum_cash for item in sampled_results]),
        total_spend=_percentiles([item.metrics.total_spend for item in sampled_results]),
        total_time_used=_percentiles([item.metrics.total_time_used for item in sampled_results]),
        sample_count=sample_count,
        seed=seed,
    )