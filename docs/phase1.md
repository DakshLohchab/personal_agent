# Phase 1 Contracts

Phase 1 is an offline Python package. Its public schema types are importable from `packages.schemas`; simulation functions are in `services.simulator`. The engine performs no file, environment, network, database, or wall-clock access.

## State and scenarios

`LifeState` contains a date, a 1-120 month horizon, non-negative `Decimal` cash/income/expenses/time, and typed goals, constraints, commitments, and variables. Monetary values must be supplied as `Decimal`; floats are rejected. A goal with both `current_value` and a positive `target_value` reports clamped `current_value / target_value` progress. Goal progress is a snapshot because Phase 1 has no goal dynamics.

Scenarios hold deltas, not copies of state. The `cash` delta is applied once in month 1; income, essential-expense, and available-time deltas apply each month. A child stores its `parent_id`; pass ancestor scenarios in `scenario_catalog` to `simulate` or `compose_scenario`:

```python
from decimal import Decimal

from packages.schemas import Scenario
from services.simulator.engine import simulate

parent = Scenario(id="move", name="Move", deltas={"cash": Decimal("-10000")})
child = Scenario(
    id="furnished-move",
    name="Furnished move",
    parent_id="move",
    deltas={"cash": Decimal("-5000")},
)
result = simulate(state, child, scenario_catalog={parent.id: parent})
```

Ancestor and child deltas for the same key add together. Missing ancestors and cycles raise `InvalidScenarioError`.

## Monthly accounting

Each month computes `starting_cash + income - essential_expenses - commitment_cost + one_time_adjustments`. Active commitment cost is included in `discretionary_spend` and total spend; negative one-time cash adjustments are also counted as spend. Commitments are active inclusively from `start_month` through `end_month`, or indefinitely if no end is set.

`time_available_hours` in each monthly result means remaining hours after active commitment time, floored at zero. Scenario-adjusted available time is also floored at zero. `time_used_hours` is the commitment hours. A matching `minimum_time_available` constraint reports any shortage; no implicit constraint ID is invented. Cash, monthly-spend, and remaining-time constraints are checked each month and returned both on their month and at result level.

## Uncertainty and analysis

`simulate(..., seed=42, enable_uncertainty=True, monte_carlo_samples=1000)` samples variables that have both `min_value` and `max_value` with `numpy.random.default_rng(seed)`. A sampled variable whose key matches one of the modeled scalar state inputs (`cash`, `monthly_income`, `monthly_essential_expenses`, or `monthly_time_available_hours`) is applied to that input. Other variables remain extension data and do not affect Phase 1 accounting. Each sample calls the deterministic simulator; percentiles use NumPy's 5th, 50th, and 95th percentiles.

`sensitivity_analysis` perturbs named modeled inputs or declared variables by a percentage and sorts by largest ending-cash impact. `find_breakpoint` uses binary search only for recognized monotonic pairs: minimum cash against cash, income, or essential expenses; maximum spend against essential expenses; and minimum remaining time against available time. Other parameters use a bounded 1000-step grid. Bounds are inclusive; the returned value is the satisfying-side approximation within tolerance, or `None` if no transition is found.

## Versions and limits

Engine and schema versions are stable constants (`0.1.0`). Phase 1 intentionally has no recurring scenario-delta syntax, qualitative goal scoring, or domain-specific interpretation for extension variables such as `laptop_cost`; model a one-time cost with a negative `cash` delta. Simulation output is deterministic for identical input values, seed, and engine version.