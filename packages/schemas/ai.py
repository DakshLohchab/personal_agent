"""Validated intermediate representations for AI-assisted decisions."""

from __future__ import annotations

from decimal import Decimal

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from packages.schemas.life_state import LifeState
from packages.schemas.scenario import Scenario


class AIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


SimulationReadiness = Literal["READY_TO_SIMULATE", "NEEDS_INFORMATION"]


class MissingFieldPrompt(AIModel):
    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    question: str = Field(min_length=1)
    field_type: Literal["currency", "integer", "text"] = "currency"
    required: bool = True


class DecisionOption(AIModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    scenario: Scenario | None = None


class DecisionInterpretation(AIModel):
    objective: str = Field(min_length=1)
    current_state: LifeState | None = None
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    commitments: list[str] = Field(default_factory=list)
    candidate_options: list[DecisionOption] = Field(default_factory=list)
    proposed_assumptions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    simulation_readiness: Literal["READY_TO_SIMULATE", "NEEDS_INFORMATION"] = "NEEDS_INFORMATION"
    required_missing_fields: list[str] = Field(default_factory=list)
    missing_field_prompts: list[MissingFieldPrompt] = Field(default_factory=list)

    @model_validator(mode="after")
    def resolve_default_readiness(self) -> "DecisionInterpretation":
        if (
            self.current_state is not None
            and any(opt.scenario is not None for opt in self.candidate_options)
            and not self.required_missing_fields
            and self.simulation_readiness == "NEEDS_INFORMATION"
            and "simulation_readiness" not in self.model_fields_set
        ):
            self.simulation_readiness = "READY_TO_SIMULATE"
        return self


class AIExplanation(AIModel):
    explanation: str = Field(min_length=1)
    caveats: list[str] = Field(default_factory=list)


class SimulateScenarioInput(AIModel):
    life_state: LifeState
    scenario: Scenario
    seed: int = 42
    enable_uncertainty: bool = False
    monte_carlo_samples: int = Field(default=1, ge=1, le=100000)


class SensitivityInput(AIModel):
    life_state: LifeState
    scenario: Scenario
    variable_keys: list[str] = Field(min_length=1)
    perturbation_percent: Decimal = Field(default=Decimal("10"), gt=0, le=100)


class BreakpointInput(AIModel):
    life_state: LifeState
    scenario: Scenario
    variable_key: str = Field(min_length=1)
    lower_bound: Decimal
    upper_bound: Decimal
    target_constraint_id: str = Field(min_length=1)
    tolerance: Decimal = Field(default=Decimal("1"), gt=0)

