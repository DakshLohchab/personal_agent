"""Typed simulator outputs."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ResultModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConstraintViolation(ResultModel):
    month: int = Field(ge=1)
    constraint_id: str
    observed: Decimal
    limit: Decimal


class MonthlyState(ResultModel):
    month: int = Field(ge=1)
    starting_cash: Decimal
    income: Decimal
    essential_expenses: Decimal
    discretionary_spend: Decimal
    one_time_adjustments: Decimal
    ending_cash: Decimal
    time_available_hours: Decimal
    time_used_hours: Decimal
    goal_progress: dict[str, Decimal]
    constraint_violations: list[ConstraintViolation]


class SummaryMetrics(ResultModel):
    ending_cash: Decimal
    minimum_cash: Decimal
    total_spend: Decimal
    total_time_used: Decimal


class PercentileMetrics(ResultModel):
    p05: Decimal
    p50: Decimal
    p95: Decimal


class UncertaintyResult(ResultModel):
    ending_cash: PercentileMetrics
    minimum_cash: PercentileMetrics
    total_spend: PercentileMetrics
    total_time_used: PercentileMetrics
    sample_count: int = Field(ge=1)
    seed: int


class SimulationResult(ResultModel):
    monthly_states: list[MonthlyState]
    final_state: MonthlyState
    metrics: SummaryMetrics
    uncertainty: UncertaintyResult | None
    constraint_violations: list[ConstraintViolation]
    engine_version: str
    schema_version: str


class SensitivityResult(ResultModel):
    variable_key: str
    baseline_ending_cash: Decimal
    low_ending_cash: Decimal
    high_ending_cash: Decimal
    absolute_impact: Decimal