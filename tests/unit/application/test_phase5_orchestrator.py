from decimal import Decimal

from packages.schemas.ai import DecisionInterpretation, DecisionOption
from packages.schemas.scenario import Scenario
from services.agents.orchestrator import DecisionOrchestrator
from tests.fixtures.golden_cases import base_state


def test_orchestrator_uses_deterministic_simulator_for_numeric_results() -> None:
    interpretation = DecisionInterpretation(
        objective="choose",
        current_state=base_state(),
        candidate_options=[
            DecisionOption(
                name="save",
                description="save",
                scenario=Scenario(id="save", name="Save", deltas={"cash": Decimal(5000)}),
            )
        ],
    )

    result = DecisionOrchestrator().run(interpretation, model="fake")

    assert result.status == "completed"
    assert result.simulation_outputs[0].result.metrics.ending_cash == Decimal(71000)
    assert set(result.specialist_results) == {
        "FinanceAgent",
        "TimeAgent",
        "ResearchAgent",
        "RiskAgent",
        "OpportunityAgent",
        "FutureYouAgent",
        "SynthesisAgent",
    }
