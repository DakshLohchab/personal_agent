"""Allowlisted deterministic tools for the AI application service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, TypeAdapter, ValidationError

from packages.schemas.ai import (
    BreakpointInput,
    SensitivityInput,
    SimulateScenarioInput,
)
from packages.schemas.simulation import SensitivityResult, SimulationResult
from services.application.analysis_service import AnalysisService
from services.application.simulation_service import SimulationService


class ToolExecutionError(ValueError):
    """A requested tool is unknown or has invalid arguments."""


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_model: type[BaseModel]
    output_model: Any
    execute: Callable[[Any], Any]


class DeterministicToolRegistry:
    def __init__(
        self,
        simulation_service: SimulationService | None = None,
        analysis_service: AnalysisService | None = None,
    ) -> None:
        simulation = simulation_service or SimulationService()
        analysis = analysis_service or AnalysisService()
        self._tools = {
            "simulate_scenario": ToolSpec(
                "simulate_scenario",
                "Run the deterministic simulator for a validated scenario.",
                SimulateScenarioInput,
                SimulationResult,
                lambda args: simulation.run(
                    args.life_state,
                    args.scenario,
                    seed=args.seed,
                    enable_uncertainty=args.enable_uncertainty,
                    monte_carlo_samples=args.monte_carlo_samples,
                ),
            ),
            "run_sensitivity": ToolSpec(
                "run_sensitivity",
                "Run deterministic one-at-a-time sensitivity analysis.",
                SensitivityInput,
                list[SensitivityResult],
                lambda args: analysis.sensitivity_analysis(
                    args.life_state,
                    args.scenario,
                    args.variable_keys,
                    perturbation_percent=args.perturbation_percent,
                ),
            ),
            "find_breakpoint": ToolSpec(
                "find_breakpoint",
                "Find a deterministic constraint breakpoint.",
                BreakpointInput,
                dict,
                lambda args: {
                    "variable_key": args.variable_key,
                    "breakpoint": analysis.find_breakpoint(
                        args.life_state,
                        args.scenario,
                        args.variable_key,
                        args.lower_bound,
                        args.upper_bound,
                        args.target_constraint_id,
                        tolerance=args.tolerance,
                    ),
                    "target_constraint_id": args.target_constraint_id,
                },
            ),
        }

    def definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "parameters": spec.input_model.model_json_schema(),
            }
            for spec in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> BaseModel:
        spec = self._tools.get(name)
        if spec is None:
            raise ToolExecutionError(f"unknown deterministic tool: {name}")
        try:
            validated = spec.input_model.model_validate(arguments)
        except ValidationError as error:
            raise ToolExecutionError(f"invalid arguments for {name}") from error
        result = spec.execute(validated)
        return TypeAdapter(spec.output_model).validate_python(result)
