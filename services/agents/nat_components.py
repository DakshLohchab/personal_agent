"""NVIDIA NeMo Agent Toolkit adapters for the Phase 5 application boundary."""

from __future__ import annotations

import json
from typing import Any

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from packages.schemas.ai import DecisionInterpretation
from services.agents.orchestrator import DecisionOrchestrator
from services.api.dependencies import get_settings
from services.application.ai_tools import DeterministicToolRegistry


class LifeSandboxOrchestratorConfig(
    FunctionBaseConfig, name="life_sandbox_orchestrator"
):
    """NAT configuration for the existing supervisor-owned orchestrator."""


class LifeSandboxSimulateScenarioConfig(
    FunctionBaseConfig, name="life_sandbox_simulate_scenario"
):
    """NAT configuration for the allowlisted deterministic simulation tool."""


class LifeSandboxSensitivityConfig(
    FunctionBaseConfig, name="life_sandbox_run_sensitivity"
):
    """NAT configuration for the allowlisted sensitivity tool."""


class LifeSandboxBreakpointConfig(
    FunctionBaseConfig, name="life_sandbox_find_breakpoint"
):
    """NAT configuration for the allowlisted breakpoint tool."""


def _tool_function(
    registry: DeterministicToolRegistry, tool_name: str
):
    async def execute(payload: str) -> str:
        arguments: dict[str, Any] = json.loads(payload)
        result = registry.execute(tool_name, arguments)
        return result.model_dump_json()

    return execute


@register_function(config_type=LifeSandboxSimulateScenarioConfig)
async def register_simulate_scenario(
    _config: LifeSandboxSimulateScenarioConfig, _builder: Builder
):
    registry = DeterministicToolRegistry()
    yield FunctionInfo.from_fn(
        _tool_function(registry, "simulate_scenario"),
        description=(
            "Run the existing validated deterministic simulator. Input is a JSON "
            "object matching SimulateScenarioInput."
        ),
    )


@register_function(config_type=LifeSandboxSensitivityConfig)
async def register_run_sensitivity(
    _config: LifeSandboxSensitivityConfig, _builder: Builder
):
    registry = DeterministicToolRegistry()
    yield FunctionInfo.from_fn(
        _tool_function(registry, "run_sensitivity"),
        description=(
            "Run the existing validated deterministic sensitivity tool. Input is "
            "a JSON object matching SensitivityInput."
        ),
    )


@register_function(config_type=LifeSandboxBreakpointConfig)
async def register_find_breakpoint(
    _config: LifeSandboxBreakpointConfig, _builder: Builder
):
    registry = DeterministicToolRegistry()
    yield FunctionInfo.from_fn(
        _tool_function(registry, "find_breakpoint"),
        description=(
            "Run the existing validated deterministic breakpoint tool. Input is "
            "a JSON object matching BreakpointInput."
        ),
    )


@register_function(config_type=LifeSandboxOrchestratorConfig)
async def register_orchestrator(
    _config: LifeSandboxOrchestratorConfig, _builder: Builder
):
    orchestrator = DecisionOrchestrator()

    async def execute(payload: str) -> str:
        request = DecisionInterpretation.model_validate_json(payload)
        result = orchestrator.run(request, model=get_settings().nebius_model)
        return result.model_dump_json()

    yield FunctionInfo.from_fn(
        execute,
        description=(
            "Run the existing supervisor-owned Life Sandbox multi-agent "
            "orchestrator. Input is a JSON DecisionInterpretation."
        ),
    )
