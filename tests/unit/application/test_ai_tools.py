from decimal import Decimal

import pytest

from packages.schemas.ai import SimulateScenarioInput
from services.application.ai_tools import DeterministicToolRegistry, ToolExecutionError
from tests.fixtures.golden_cases import golden_cases


def test_simulate_tool_delegates_to_phase_one_engine() -> None:
    case = golden_cases()[0]
    result = DeterministicToolRegistry().execute(
        "simulate_scenario",
        SimulateScenarioInput(
            life_state=case.state,
            scenario=case.scenario,
            enable_uncertainty=False,
        ).model_dump(),
    )
    assert result.metrics.ending_cash == Decimal("66000")


def test_tool_arguments_are_validated() -> None:
    with pytest.raises(ToolExecutionError):
        DeterministicToolRegistry().execute("simulate_scenario", {"scenario": {}})
