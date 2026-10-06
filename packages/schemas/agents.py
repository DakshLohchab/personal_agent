"""Typed contracts for the Phase 5 multi-agent workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from packages.schemas.ai import DecisionInterpretation
from packages.schemas.simulation import SensitivityResult, SimulationResult


class AgentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentContext(AgentModel):
    run_id: UUID = Field(default_factory=uuid4)
    user_id: UUID | None = None
    interpretation: DecisionInterpretation
    model: str
    prompt_version: str
    memory_context: list["DecisionMemory"] = Field(default_factory=list)


class MemoryProvenance(AgentModel):
    type: str
    reference: str | None = None
    label: str


class DecisionMemory(AgentModel):
    memory_id: UUID
    memory_type: str
    content: str
    confidence: float | None = None
    provenance: MemoryProvenance
    retrieval_reason: str
    last_confirmed_at: datetime | None = None


class AgentRequest(AgentModel):
    context: AgentContext
    specialist: str


class AgentEvidenceReference(AgentModel):
    evidence_id: UUID | None = None
    url: str = Field(min_length=1)
    title: str | None = None
    publisher: str | None = None
    retrieved_at: datetime | None = None
    identifier: str | None = None


class AgentSimulationRequest(AgentModel):
    option_name: str = Field(min_length=1)
    tool_name: Literal["simulate_scenario", "run_sensitivity", "find_breakpoint"]
    arguments: dict[str, Any]


class AgentFinding(AgentModel):
    category: Literal["calculated", "external_evidence", "assumption", "qualitative"]
    statement: str = Field(min_length=1)
    option_name: str | None = None
    evidence: list[AgentEvidenceReference] = Field(default_factory=list)
    simulation_requests: list[AgentSimulationRequest] = Field(default_factory=list)
    simulation_result_refs: list[str] = Field(default_factory=list)


class AgentRunMetadata(AgentModel):
    run_id: UUID
    parent_run_id: UUID | None = None
    agent_name: str
    agent_version: str
    model_identifier: str
    prompt_version: str
    status: Literal["pending", "running", "completed", "failed", "partial"]
    started_at: datetime
    completed_at: datetime | None = None
    input_hash: str
    output_hash: str | None = None
    error_category: str | None = None
    error_message: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)


class AgentResponse(AgentModel):
    agent_name: str
    agent_version: str
    status: Literal["completed", "failed", "partial"]
    findings: list[AgentFinding] = Field(default_factory=list)
    evidence: list[AgentEvidenceReference] = Field(default_factory=list)
    simulation_requests: list[AgentSimulationRequest] = Field(default_factory=list)
    metadata: AgentRunMetadata
    error: str | None = None


class AgentSimulationOutput(AgentModel):
    option_name: str
    tool_name: str
    result: SimulationResult | list[SensitivityResult] | dict[str, Any]


class OrchestratedRunResult(AgentModel):
    run_id: UUID
    status: Literal["queued", "running", "completed", "partial", "failed"]
    specialist_results: dict[str, AgentResponse] = Field(default_factory=dict)
    simulation_outputs: list[AgentSimulationOutput] = Field(default_factory=list)
    evidence: list[AgentEvidenceReference] = Field(default_factory=list)
    final_synthesis: AgentResponse | None = None
    metadata: list[AgentRunMetadata] = Field(default_factory=list)
    memory_context: list[DecisionMemory] = Field(default_factory=list)
