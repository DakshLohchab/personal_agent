"""Transport request schemas for the API."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from packages.schemas import LifeState, Scenario


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SimulationRequest(RequestModel):
    life_state: LifeState
    scenario: Scenario
    seed: int = Field(default=42)
    enable_uncertainty: bool = Field(default=True)
    monte_carlo_samples: int = Field(default=1000, ge=1, le=100000)

    @field_validator("seed")
    @classmethod
    def validate_seed(cls, value: int) -> int:
        if isinstance(value, bool):
            raise ValueError("seed must be an integer")
        return int(value)


class SensitivityRequest(RequestModel):
    life_state: LifeState
    scenario: Scenario
    variable_keys: list[str] = Field(default_factory=list)
    perturbation_percent: Decimal = Field(default=Decimal("10"), gt=0, le=Decimal("100"))

    @field_validator("variable_keys")
    @classmethod
    def validate_variable_keys(cls, values: list[str]) -> list[str]:
        if not values or any(not item.strip() for item in values):
            raise ValueError("variable_keys must contain at least one non-empty value")
        return values


class BreakpointRequest(RequestModel):
    life_state: LifeState
    scenario: Scenario
    variable_key: str = Field(min_length=1)
    lower_bound: Decimal
    upper_bound: Decimal
    target_constraint_id: str = Field(min_length=1)
    tolerance: Decimal = Field(default=Decimal("1"), gt=0)

    @model_validator(mode="after")
    def validate_bounds(self) -> "BreakpointRequest":
        if self.lower_bound > self.upper_bound:
            raise ValueError("lower_bound must not exceed upper_bound")
        return self
