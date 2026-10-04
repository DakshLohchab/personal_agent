"""Specialized, typed agents. Numerical claims come only from tool outputs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Literal

from packages.ports.research import ResearchProvider
from packages.schemas.agents import (
    AgentContext,
    AgentEvidenceReference,
    AgentFinding,
    AgentRequest,
    AgentResponse,
    AgentRunMetadata,
)
from services.agents.errors import MalformedAgentOutput, ResearchFailure


def _metadata(
    context: AgentContext,
    name: str,
    started: datetime,
    status: Literal["pending", "running", "completed", "failed", "partial"],
    **kwargs: Any,
) -> AgentRunMetadata:
    input_hash = sha256(context.interpretation.model_dump_json().encode()).hexdigest()
    return AgentRunMetadata(
        run_id=context.run_id,
        agent_name=name,
        agent_version="1.0.0",
        model_identifier=context.model,
        prompt_version=context.prompt_version,
        status=status,
        started_at=started,
        completed_at=datetime.now(timezone.utc),
        input_hash=input_hash,
        **kwargs,
    )


class SpecialistAgent(ABC):
    name = "specialist"
    version = "1.0.0"

    def run(self, request: AgentRequest) -> AgentResponse:
        started = datetime.now(timezone.utc)
        try:
            findings, evidence = self.analyze(request.context)
            response = AgentResponse(
                agent_name=self.name,
                agent_version=self.version,
                status="completed",
                findings=findings,
                evidence=evidence,
                metadata=_metadata(request.context, self.name, started, "completed"),
            )
            return response
        except Exception as exc:
            if isinstance(exc, (MalformedAgentOutput, ResearchFailure)):
                error = exc
            else:
                error = MalformedAgentOutput(f"{self.name} failed: {exc}")
            return AgentResponse(
                agent_name=self.name,
                agent_version=self.version,
                status="failed",
                error=str(error),
                metadata=_metadata(
                    request.context,
                    self.name,
                    started,
                    "failed",
                    error_category=type(error).__name__,
                    error_message=str(error),
                ),
            )

    @abstractmethod
    def analyze(
        self, context: AgentContext
    ) -> tuple[list[AgentFinding], list[AgentEvidenceReference]]: ...


class FinanceAgent(SpecialistAgent):
    name = "FinanceAgent"

    def analyze(
        self, context: AgentContext
    ) -> tuple[list[AgentFinding], list[AgentEvidenceReference]]:
        return [
            AgentFinding(
                category="qualitative",
                statement=(
                    "Compare affordability and cash-flow consequences using deterministic "
                    "simulation outputs."
                ),
            )
        ], []


class TimeAgent(SpecialistAgent):
    name = "TimeAgent"

    def analyze(
        self, context: AgentContext
    ) -> tuple[list[AgentFinding], list[AgentEvidenceReference]]:
        return [
            AgentFinding(
                category="qualitative",
                statement=(
                    "Evaluate schedule commitments and time feasibility for each candidate "
                    "option."
                ),
            )
        ], []


class ResearchAgent(SpecialistAgent):
    name = "ResearchAgent"

    def __init__(self, provider: ResearchProvider | None = None) -> None:
        self.provider = provider

    def analyze(
        self, context: AgentContext
    ) -> tuple[list[AgentFinding], list[AgentEvidenceReference]]:
        if self.provider is None or not context.interpretation.missing_information:
            return [], []
        query = " ".join(context.interpretation.missing_information)
        try:
            results = self.provider.search(query, max_results=5)
        except Exception as exc:
            raise ResearchFailure("research provider failed") from exc
        evidence = [
            AgentEvidenceReference(
                url=result.url,
                title=result.title,
                publisher=result.publisher,
                retrieved_at=result.retrieved_at,
                identifier=result.metadata.get("id"),
            )
            for result in results
            if result.url.strip()
        ]
        return [
            AgentFinding(
                category="external_evidence",
                statement="External facts are represented only by cited research sources.",
                evidence=evidence,
            )
        ] if evidence else [], evidence


class RiskAgent(SpecialistAgent):
    name = "RiskAgent"

    def analyze(
        self, context: AgentContext
    ) -> tuple[list[AgentFinding], list[AgentEvidenceReference]]:
        return [
            AgentFinding(
                category="qualitative",
                statement=(
                    "Identify downside outcomes, uncertainty, and constraint violations from "
                    "simulator results."
                ),
            )
        ], []


class OpportunityAgent(SpecialistAgent):
    name = "OpportunityAgent"

    def analyze(
        self, context: AgentContext
    ) -> tuple[list[AgentFinding], list[AgentEvidenceReference]]:
        return [
            AgentFinding(
                category="qualitative",
                statement=(
                    "Identify alternatives and second-order opportunities without ranking them "
                    "with an opaque score."
                ),
            )
        ], []


class FutureYouAgent(SpecialistAgent):
    name = "FutureYouAgent"

    def analyze(
        self, context: AgentContext
    ) -> tuple[list[AgentFinding], list[AgentEvidenceReference]]:
        return [
            AgentFinding(
                category="qualitative",
                statement="Interpret longer-term trade-offs using already-produced scenario data.",
            )
        ], []


class SynthesisAgent(SpecialistAgent):
    name = "SynthesisAgent"

    def analyze(
        self, context: AgentContext
    ) -> tuple[list[AgentFinding], list[AgentEvidenceReference]]:
        return [
            AgentFinding(
                category="qualitative",
                statement=(
                    "Present a transparent comparison separating calculated results, evidence, "
                    "assumptions, and interpretation."
                ),
            )
        ], []


SPECIALIST_TYPES = (
    FinanceAgent,
    TimeAgent,
    ResearchAgent,
    RiskAgent,
    OpportunityAgent,
)
