"""Pure deterministic monthly life-state simulation."""

from collections.abc import Mapping
from decimal import Decimal

from packages.schemas.common import (
    ENGINE_VERSION,
    SCHEMA_VERSION,
    InvalidScenarioError,
    InvalidSimulationInputError,
)
from packages.schemas.life_state import Commitment, LifeState
from packages.schemas.scenario import Scenario
from packages.schemas.simulation import (
    ConstraintViolation,
    MonthlyState,
    SimulationResult,
    SummaryMetrics,
)

ZERO = Decimal(0)
STATE_DELTA_KEYS = frozenset(
    {"cash", "monthly_income", "monthly_essential_expenses", "monthly_time_available_hours"}
)


def compose_scenario(
    scenario: Scenario,
    scenario_catalog: Mapping[str, Scenario] | None = None,
) -> Scenario:
    """Resolve a branch by summing ancestor deltas before child deltas."""
    catalog = scenario_catalog or {}
    chain: list[Scenario] = []
    seen = {scenario.id}
    current = scenario
    while current.parent_id is not None:
        parent = catalog.get(current.parent_id)
        if parent is None:
            raise InvalidScenarioError(f"missing parent scenario: {current.parent_id}")
        if parent.id in seen:
            raise InvalidScenarioError("scenario parent cycle detected")
        seen.add(parent.id)
        chain.append(parent)
        current = parent

    combined: dict[str, Decimal] = {}
    assumptions: list[str] = []
    for branch in list(reversed(chain)) + [scenario]:
        for key, delta in branch.deltas.items():
            combined[key] = combined.get(key, ZERO) + delta
        assumptions.extend(item for item in branch.assumption_ids if item not in assumptions)
    return Scenario(
        id=scenario.id,
        name=scenario.name,
        deltas=combined,
        assumption_ids=assumptions,
    )


def _active_commitments(commitments: list[Commitment], month: int) -> list[Commitment]:
    return [
        commitment
        for commitment in commitments
        if commitment.start_month <= month
        and (commitment.end_month is None or month <= commitment.end_month)
    ]


def _goal_progress(state: LifeState) -> dict[str, Decimal]:
    progress: dict[str, Decimal] = {}
    for goal in state.goals:
        if goal.target_value is None or goal.current_value is None or goal.target_value <= 0:
            continue
        progress[goal.id] = min(Decimal(1), max(ZERO, goal.current_value / goal.target_value))
    return progress


def _constraint_violations(
    state: LifeState,
    month: int,
    ending_cash: Decimal,
    monthly_spend: Decimal,
    remaining_time: Decimal,
) -> list[ConstraintViolation]:
    observations = {
        "minimum_cash": ending_cash,
        "maximum_monthly_spend": monthly_spend,
        "minimum_time_available": remaining_time,
    }
    violations: list[ConstraintViolation] = []
    for constraint in state.constraints:
        observed = observations[constraint.metric]
        violated = (
            observed < constraint.limit
            if constraint.metric in {"minimum_cash", "minimum_time_available"}
            else observed > constraint.limit
        )
        if violated:
            violations.append(
                ConstraintViolation(
                    month=month,
                    constraint_id=constraint.id,
                    observed=observed,
                    limit=constraint.limit,
                )
            )
    return violations


def _monthly_spend(
    essential_expenses: Decimal,
    commitment_cost: Decimal,
    one_time_adjustment: Decimal,
) -> Decimal:
    return essential_expenses + commitment_cost + max(ZERO, -one_time_adjustment)


def simulate(
    state: LifeState,
    scenario: Scenario,
    *,
    seed: int = 42,
    enable_uncertainty: bool = True,
    monte_carlo_samples: int = 1000,
    scenario_catalog: Mapping[str, Scenario] | None = None,
) -> SimulationResult:
    """Simulate monthly cash and time, optionally attaching seeded uncertainty."""
    if monte_carlo_samples < 1:
        raise InvalidSimulationInputError("monte_carlo_samples must be positive")
    effective_scenario = compose_scenario(scenario, scenario_catalog)
    unsupported = set(effective_scenario.deltas) - STATE_DELTA_KEYS
    if unsupported:
        raise InvalidScenarioError(f"unsupported scenario delta keys: {sorted(unsupported)}")
    adjusted = state.model_dump()
    for key in STATE_DELTA_KEYS - {"cash"}:
        adjusted[key] = getattr(state, key) + effective_scenario.deltas.get(key, ZERO)
    if adjusted["monthly_income"] < ZERO or adjusted["monthly_essential_expenses"] < ZERO:
        raise InvalidSimulationInputError("scenario produces a negative recurring amount")
    adjusted["monthly_time_available_hours"] = max(
        ZERO, adjusted["monthly_time_available_hours"]
    )
    concrete_state = LifeState.model_validate(adjusted)

    monthly_states: list[MonthlyState] = []
    violations: list[ConstraintViolation] = []
    starting_cash = state.cash
    total_spend = ZERO
    total_time_used = ZERO
    for month in range(1, state.horizon_months + 1):
        active = _active_commitments(state.commitments, month)
        commitment_cost = sum((item.monthly_cost for item in active), ZERO)
        time_used = sum((item.monthly_hours for item in active), ZERO)
        essential_expenses = concrete_state.monthly_essential_expenses
        one_time = effective_scenario.deltas.get("cash", ZERO) if month == 1 else ZERO
        ending_cash = (
            starting_cash
            + concrete_state.monthly_income
            - essential_expenses
            - commitment_cost
            + one_time
        )
        remaining_time = max(ZERO, concrete_state.monthly_time_available_hours - time_used)
        month_violations = _constraint_violations(
            concrete_state,
            month,
            ending_cash,
            _monthly_spend(essential_expenses, commitment_cost, one_time),
            remaining_time,
        )
        monthly_state = MonthlyState(
            month=month,
            starting_cash=starting_cash,
            income=concrete_state.monthly_income,
            essential_expenses=essential_expenses,
            discretionary_spend=commitment_cost + max(ZERO, -one_time),
            one_time_adjustments=one_time,
            ending_cash=ending_cash,
            time_available_hours=remaining_time,
            time_used_hours=time_used,
            goal_progress=_goal_progress(concrete_state),
            constraint_violations=month_violations,
        )
        monthly_states.append(monthly_state)
        violations.extend(month_violations)
        starting_cash = ending_cash
        total_spend += _monthly_spend(essential_expenses, commitment_cost, one_time)
        total_time_used += time_used

    metrics = SummaryMetrics(
        ending_cash=monthly_states[-1].ending_cash,
        minimum_cash=min(item.ending_cash for item in monthly_states),
        total_spend=total_spend,
        total_time_used=total_time_used,
    )
    result = SimulationResult(
        monthly_states=monthly_states,
        final_state=monthly_states[-1],
        metrics=metrics,
        uncertainty=None,
        constraint_violations=violations,
        engine_version=ENGINE_VERSION,
        schema_version=SCHEMA_VERSION,
    )
    if enable_uncertainty:
        from .uncertainty import calculate_uncertainty

        result.uncertainty = calculate_uncertainty(
            state,
            scenario,
            seed=seed,
            sample_count=monte_carlo_samples,
            scenario_catalog=scenario_catalog,
        )
    return result