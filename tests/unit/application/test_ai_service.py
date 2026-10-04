from datetime import date
from decimal import Decimal
from typing import Any

from packages.ports.llm import LLMResponse, LLMToolCall
from packages.schemas import LifeState, Scenario
from services.application.ai_service import AIService
from services.application.ai_tools import DeterministicToolRegistry, ToolExecutionError
from tests.fixtures.golden_cases import base_state


class FakeLLMProvider:
    def __init__(self, state: LifeState, scenario: Scenario) -> None:
        self.state = state
        self.scenario = scenario
        self.calls = []

    def complete(self, request: Any) -> LLMResponse:
        self.calls.append(request)
        if len(self.calls) == 1:
            return LLMResponse(
                structured_content={
                    "objective": "Choose how to use available money",
                    "current_state": self.state.model_dump(mode="json"),
                    "candidate_options": [
                        {
                            "name": "save",
                            "description": "Keep the money as savings",
                            "scenario": self.scenario.model_dump(mode="json"),
                        }
                    ],
                },
                tool_calls=[
                    LLMToolCall(
                        id="tool-1",
                        name="simulate_scenario",
                        arguments={
                            "life_state": self.state.model_dump(mode="json"),
                            "scenario": self.scenario.model_dump(mode="json"),
                        },
                    )
                ],
                model=request.model,
                provider="fake",
            )
        result = request.messages[-1].content
        return LLMResponse(
            structured_content={
                "explanation": f"Simulator result: {result}",
                "caveats": ["The simulator is the numerical source of truth."],
            },
            model=request.model,
            provider="fake",
        )


def test_golden_decision_uses_simulator_for_numerical_result() -> None:
    state = base_state(start_date=date(2026, 1, 1), cash=Decimal("50000"))
    scenario = Scenario(id="save", name="Save", deltas={"cash": Decimal("5000")})
    provider = FakeLLMProvider(state, scenario)

    result = AIService(provider).interpret(
        "I have ₹50,000 and can travel, buy a laptop, or save.",
        model="fake-model",
    )

    simulation_result = result["tool_results"][0]["result"]
    assert simulation_result["metrics"]["ending_cash"] == "71000"
    assert "71000" in result["explanation"].explanation
    assert result["metadata"]["prompt_version"] == "phase4.v1"


def test_unknown_tool_is_rejected() -> None:
    try:
        DeterministicToolRegistry().execute("not-allowed", {})
    except ToolExecutionError as error:
        assert "unknown deterministic tool" in str(error)
    else:
        raise AssertionError("unknown tools must be rejected")


def test_malformed_structured_output_is_rejected() -> None:
    class MalformedProvider:
        def complete(self, request: Any) -> LLMResponse:
            return LLMResponse(structured_content={"objective": 12}, model="x", provider="fake")

    try:
        AIService(MalformedProvider()).interpret("decide", model="x")
    except ValueError as error:
        assert "invalid decision interpretation" in str(error)
    else:
        raise AssertionError("malformed model output must be rejected")
