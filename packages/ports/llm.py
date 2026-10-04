"""Provider-neutral contracts for structured language-model calls."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class LLMError(RuntimeError):
    """Base class for failures returned by an LLM provider."""


class LLMConfigurationError(LLMError):
    """Provider configuration is invalid."""


class LLMProviderError(LLMError):
    """A provider request failed safely."""


class LLMMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(pattern="^(system|user|assistant|tool)$")
    content: str
    tool_call_id: str | None = None


class LLMGenerationSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(default=0.0, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1)


class LLMStructuredOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    json_schema: dict[str, Any]
    strict: bool = True


class LLMToolDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    parameters: dict[str, Any]


class LLMToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    arguments: dict[str, Any]


class LLMToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_call_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    content: dict[str, Any]


class LLMRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[LLMMessage] = Field(min_length=1)
    model: str = Field(min_length=1)
    generation: LLMGenerationSettings = Field(default_factory=LLMGenerationSettings)
    structured_output: LLMStructuredOutput | None = None
    tools: list[LLMToolDefinition] = Field(default_factory=list)


class LLMUsage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str | None = None
    structured_content: dict[str, Any] | None = None
    tool_calls: list[LLMToolCall] = Field(default_factory=list)
    model: str
    provider: str
    request_id: str | None = None
    usage: LLMUsage | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMProvider(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...
