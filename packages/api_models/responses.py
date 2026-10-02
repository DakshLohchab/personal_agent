"""Transport response schemas for the API."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer

from packages.schemas.simulation import (
    ConstraintViolation,
    MonthlyState,
    SensitivityResult,
    SimulationResult,
    SummaryMetrics,
    UncertaintyResult,
)


def _as_decimal_string(value: Decimal) -> str:
    return format(value, "f")


class ResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(ResponseModel):
    status: str
    service: str
    version: str


class ConstraintViolationResponse(ResponseModel):
    month: int
    constraint_id: str
    observed: Decimal
    limit: Decimal

    @field_serializer("observed", "limit", when_used="json")
    def serialize_decimal(self, value: Decimal) -> str:
        return _as_decimal_string(value)

    @classmethod
    def from_domain(cls, item: ConstraintViolation) -> "ConstraintViolationResponse":
        return cls.model_validate(item.model_dump())


class MonthlyStateResponse(ResponseModel):
    month: int
    starting_cash: Decimal
    income: Decimal
    essential_expenses: Decimal
    discretionary_spend: Decimal
    one_time_adjustments: Decimal
    ending_cash: Decimal
    time_available_hours: Decimal
    time_used_hours: Decimal
    goal_progress: dict[str, Decimal]
    constraint_violations: list[ConstraintViolationResponse]

    @field_serializer(
        "starting_cash",
        "income",
        "essential_expenses",
        "discretionary_spend",
        "one_time_adjustments",
        "ending_cash",
        when_used="json",
    )
    def serialize_money(self, value: Decimal) -> str:
        return _as_decimal_string(value)

    @field_serializer("goal_progress", when_used="json")
    def serialize_ratio(self, value: dict[str, Decimal]) -> dict[str, str]:
        return {key: _as_decimal_string(item) for key, item in value.items()}

    @field_serializer("time_available_hours", "time_used_hours", when_used="json")
    def serialize_time(self, value: Decimal) -> str:
        return _as_decimal_string(value)

    @classmethod
    def from_domain(cls, item: MonthlyState) -> "MonthlyStateResponse":
        return cls(
            month=item.month,
            starting_cash=item.starting_cash,
            income=item.income,
            essential_expenses=item.essential_expenses,
            discretionary_spend=item.discretionary_spend,
            one_time_adjustments=item.one_time_adjustments,
            ending_cash=item.ending_cash,
            time_available_hours=item.time_available_hours,
            time_used_hours=item.time_used_hours,
            goal_progress=item.goal_progress,
            constraint_violations=[
                ConstraintViolationResponse.from_domain(entry)
                for entry in item.constraint_violations
            ],
        )


class PercentileMetricsResponse(ResponseModel):
    p05: Decimal
    p50: Decimal
    p95: Decimal

    @field_serializer("p05", "p50", "p95", when_used="json")
    def serialize_decimal(self, value: Decimal) -> str:
        return _as_decimal_string(value)

    @classmethod
    def from_domain(cls, item: Any) -> "PercentileMetricsResponse":
        return cls.model_validate(item.model_dump())


class UncertaintyResponse(ResponseModel):
    ending_cash: PercentileMetricsResponse
    minimum_cash: PercentileMetricsResponse
    total_spend: PercentileMetricsResponse
    total_time_used: PercentileMetricsResponse
    sample_count: int
    seed: int

    @classmethod
    def from_domain(cls, item: UncertaintyResult | None) -> "UncertaintyResponse | None":
        if item is None:
            return None
        return cls(
            ending_cash=PercentileMetricsResponse.from_domain(item.ending_cash),
            minimum_cash=PercentileMetricsResponse.from_domain(item.minimum_cash),
            total_spend=PercentileMetricsResponse.from_domain(item.total_spend),
            total_time_used=PercentileMetricsResponse.from_domain(item.total_time_used),
            sample_count=item.sample_count,
            seed=item.seed,
        )


class SummaryMetricsResponse(ResponseModel):
    ending_cash: Decimal
    minimum_cash: Decimal
    total_spend: Decimal
    total_time_used: Decimal

    @field_serializer("ending_cash", "minimum_cash", "total_spend", when_used="json")
    def serialize_money(self, value: Decimal) -> str:
        return _as_decimal_string(value)

    @field_serializer("total_time_used", when_used="json")
    def serialize_time(self, value: Decimal) -> str:
        return _as_decimal_string(value)

    @classmethod
    def from_domain(cls, item: SummaryMetrics) -> "SummaryMetricsResponse":
        return cls.model_validate(item.model_dump())


class SimulationResponse(ResponseModel):
    summary: SummaryMetricsResponse
    monthly_states: list[MonthlyStateResponse]
    uncertainty: UncertaintyResponse | None
    constraint_violations: list[ConstraintViolationResponse]
    engine_version: str
    schema_version: str

    @classmethod
    def from_domain(cls, item: SimulationResult) -> "SimulationResponse":
        return cls(
            summary=SummaryMetricsResponse.from_domain(item.metrics),
            monthly_states=[
                MonthlyStateResponse.from_domain(entry) for entry in item.monthly_states
            ],
            uncertainty=UncertaintyResponse.from_domain(item.uncertainty),
            constraint_violations=[
                ConstraintViolationResponse.from_domain(entry)
                for entry in item.constraint_violations
            ],
            engine_version=item.engine_version,
            schema_version=item.schema_version,
        )


class SensitivityResultResponse(ResponseModel):
    variable_key: str
    baseline_ending_cash: Decimal
    low_ending_cash: Decimal
    high_ending_cash: Decimal
    absolute_impact: Decimal

    @field_serializer(
        "baseline_ending_cash",
        "low_ending_cash",
        "high_ending_cash",
        "absolute_impact",
        when_used="json",
    )
    def serialize_money(self, value: Decimal) -> str:
        return _as_decimal_string(value)

    @classmethod
    def from_domain(cls, item: SensitivityResult) -> "SensitivityResultResponse":
        return cls.model_validate(item.model_dump())


class BreakpointResponse(ResponseModel):
    variable_key: str
    breakpoint: Decimal | None
    target_constraint_id: str

    @field_serializer("breakpoint", when_used="json")
    def serialize_decimal(self, value: Decimal | None) -> str | None:
        if value is None:
            return None
        return _as_decimal_string(value)
