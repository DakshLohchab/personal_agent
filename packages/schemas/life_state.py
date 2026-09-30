"""Validated life state and its supporting domain models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Goal(DomainModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    target_value: Decimal | None = None
    current_value: Decimal | None = None
    unit: str | None = None

    @field_validator("target_value", "current_value", mode="before")
    @classmethod
    def reject_float_values(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("goal values must use Decimal, not float")
        return value


class Constraint(DomainModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    metric: Literal[
        "minimum_cash", "maximum_monthly_spend", "minimum_time_available"
    ]
    limit: Decimal

    @field_validator("limit", mode="before")
    @classmethod
    def reject_float_limit(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("constraint limits must use Decimal, not float")
        return value


class Commitment(DomainModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    monthly_cost: Decimal = Decimal(0)
    monthly_hours: Decimal = Decimal(0)
    start_month: int = Field(default=1, ge=1, strict=True)
    end_month: int | None = Field(default=None, ge=1, strict=True)

    @field_validator("monthly_cost", "monthly_hours", mode="before")
    @classmethod
    def reject_float_amounts(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("commitment amounts must use Decimal, not float")
        return value

    @field_validator("monthly_cost", "monthly_hours")
    @classmethod
    def require_non_negative_commitment_values(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("commitment cost and hours must be non-negative")
        return value

    @model_validator(mode="after")
    def validate_period(self) -> "Commitment":
        if self.end_month is not None and self.end_month < self.start_month:
            raise ValueError("end_month must be greater than or equal to start_month")
        return self


class Variable(DomainModel):
    key: str = Field(min_length=1)
    value: Decimal
    unit: str = Field(min_length=1)
    min_value: Decimal | None = None
    max_value: Decimal | None = None
    uncertainty: str | None = None

    @field_validator("value", "min_value", "max_value", mode="before")
    @classmethod
    def reject_float_values(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("variable values must use Decimal, not float")
        return value

    @model_validator(mode="after")
    def validate_bounds(self) -> "Variable":
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError("min_value must not exceed max_value")
        if self.min_value is not None and self.value < self.min_value:
            raise ValueError("value must be greater than or equal to min_value")
        if self.max_value is not None and self.value > self.max_value:
            raise ValueError("value must be less than or equal to max_value")
        return self


class LifeState(DomainModel):
    start_date: date
    horizon_months: int = Field(ge=1, le=120, strict=True)
    cash: Decimal
    monthly_income: Decimal
    monthly_essential_expenses: Decimal
    monthly_time_available_hours: Decimal
    goals: list[Goal] = Field(default_factory=list)
    constraints: list[Constraint] = Field(default_factory=list)
    commitments: list[Commitment] = Field(default_factory=list)
    variables: list[Variable] = Field(default_factory=list)

    @field_validator(
        "cash",
        "monthly_income",
        "monthly_essential_expenses",
        "monthly_time_available_hours",
        mode="before",
    )
    @classmethod
    def reject_float_amounts(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("life-state amounts must use Decimal, not float")
        return value

    @field_validator(
        "cash",
        "monthly_income",
        "monthly_essential_expenses",
        "monthly_time_available_hours",
    )
    @classmethod
    def require_non_negative(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("life-state amounts must be non-negative")
        return value

    @field_validator("start_date", mode="before")
    @classmethod
    def reject_datetime_as_date(cls, value: object) -> object:
        if isinstance(value, datetime):
            raise ValueError("start_date must be a date, not a datetime")
        return value