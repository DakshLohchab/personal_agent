"""Supervisor-owned Phase 5 workflow."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from packages.schemas.agents import (
    AgentContext,
    AgentRequest,
    AgentResponse,
    AgentRunMetadata,
    AgentSimulationOutput,
    DecisionMemory,
    OrchestratedRunResult,
)
from packages.schemas.ai import DecisionInterpretation
from packages.schemas.common import InsufficientInformationError
from packages.schemas.simulation import SimulationResult
from services.agents.errors import OrchestrationFailure
from services.agents.specialists import (
    FinanceAgent,
    FutureYouAgent,
    OpportunityAgent,
    ResearchAgent,
    RiskAgent,
    SpecialistAgent,
    SynthesisAgent,
    TimeAgent,
)
from services.application.ai_tools import DeterministicToolRegistry
from services.observability.context import set_correlation_id


class DecisionOrchestrator:
    """The only component allowed to control specialist execution order."""

    def __init__(
        self,
        tools: DeterministicToolRegistry | None = None,
        research_provider: Any | None = None,
        specialists: list[SpecialistAgent] | None = None,
        max_workers: int = 5,
        max_agent_executions: int = 8,
        max_tool_calls: int = 100,
    ) -> None:
        self.tools = tools or DeterministicToolRegistry()
        self.specialists = specialists or [
            FinanceAgent(),
            TimeAgent(),
            ResearchAgent(research_provider),
            RiskAgent(),
            OpportunityAgent(),
        ]
        self.max_workers = max_workers
        self.max_agent_executions = max_agent_executions
        self.max_tool_calls = max_tool_calls

    def run(
        self,
        interpretation: DecisionInterpretation,
        *,
        model: str,
        user_id: UUID | None = None,
        run_id: UUID | None = None,
        memory_context: list[DecisionMemory] | None = None,
    ) -> OrchestratedRunResult:
        if (
            interpretation.simulation_readiness != "READY_TO_SIMULATE"
            or interpretation.current_state is None
            or not any(option.scenario is not None for option in interpretation.candidate_options)
        ):
            raise InsufficientInformationError(
                "Provide the required decision inputs before running a comparison.",
                interpretation.required_missing_fields,
            )
        context = AgentContext(
            run_id=run_id or uuid4(),
            user_id=user_id,
            interpretation=interpretation,
            model=model,
            prompt_version="phase5-v1",
            memory_context=memory_context or [],
        )
        set_correlation_id(context.run_id)
        if len(self.specialists) + 2 > self.max_agent_executions:
            raise OrchestrationFailure("agent execution budget exceeded")
        results: dict[str, AgentResponse] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    agent.run, AgentRequest(context=context, specialist=agent.name)
                ): agent
                for agent in self.specialists
            }
            for future in as_completed(futures):
                agent = futures[future]
                try:
                    results[agent.name] = future.result()
                except Exception as exc:
                    results[agent.name] = self._failed_response(context, agent.name, exc)

        simulations = self._run_simulations(interpretation)
        aggregate = list(results.values())
        future_agent = FutureYouAgent()
        future = future_agent.run(AgentRequest(context=context, specialist=future_agent.name))
        aggregate.append(future)
        synthesis = SynthesisAgent().run(AgentRequest(context=context, specialist="SynthesisAgent"))
        aggregate.append(synthesis)
        evidence = [item for response in aggregate for item in response.evidence]
        status = "completed" if all(item.status == "completed" for item in aggregate) else "partial"
        return OrchestratedRunResult(
            run_id=context.run_id,
            status=status,
            specialist_results={item.agent_name: item for item in aggregate},
            simulation_outputs=simulations,
            evidence=evidence,
            final_synthesis=synthesis,
            metadata=[item.metadata for item in aggregate],
            memory_context=context.memory_context,
        )

    def _run_simulations(
        self, interpretation: DecisionInterpretation
    ) -> list[AgentSimulationOutput]:
        if interpretation.current_state is None:
            return []
        outputs: list[AgentSimulationOutput] = []
        for option in interpretation.candidate_options:
            if option.scenario is None:
                continue
            try:
                if len(outputs) >= self.max_tool_calls:
                    raise OrchestrationFailure("tool execution budget exceeded")
                result = self.tools.execute(
                    "simulate_scenario",
                    {
                        "life_state": interpretation.current_state.model_dump(mode="json"),
                        "scenario": option.scenario.model_dump(mode="json"),
                    },
                )
            except Exception as exc:
                raise OrchestrationFailure(f"simulation failed for {option.name}") from exc
            simulation_result = SimulationResult.model_validate(result)
            outputs.append(
                AgentSimulationOutput(
                    option_name=option.name,
                    tool_name="simulate_scenario",
                    result=simulation_result,
                )
            )
        return outputs

    @staticmethod
    def _failed_response(context: AgentContext, name: str, error: Exception) -> AgentResponse:
        now = datetime.now(timezone.utc)
        metadata = AgentRunMetadata(
            run_id=context.run_id,
            agent_name=name,
            agent_version="1.0.0",
            model_identifier=context.model,
            prompt_version=context.prompt_version,
            status="failed",
            started_at=now,
            completed_at=now,
            input_hash="",
            error_category=type(error).__name__,
            error_message=str(error),
        )
        return AgentResponse(
            agent_name=name,
            agent_version="1.0.0",
            status="failed",
            metadata=metadata,
            error=str(error),
        )
