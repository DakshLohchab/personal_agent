"""AI endpoint transport contracts."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from packages.schemas.agents import DecisionMemory, OrchestratedRunResult
from packages.schemas.ai import AIExplanation, DecisionInterpretation


class AIRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str = Field(min_length=1, max_length=10000)
    context: str | None = Field(default=None, max_length=20000)
    model: str | None = Field(default=None, min_length=1)
    interpretation: DecisionInterpretation | None = None
    background: bool = False
    memory_context: list[DecisionMemory] = Field(default_factory=list)


class AIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interpretation: DecisionInterpretation
    tool_results: list[dict[str, Any]]
    explanation: AIExplanation
    metadata: dict[str, Any]


class AgentRunResponse(OrchestratedRunResult):
    """Transport response for the supervisor endpoint."""
