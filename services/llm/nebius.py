"""Nebius Token Factory adapter using its OpenAI-compatible API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError

from packages.ports.llm import (
    LLMConfigurationError,
    LLMProviderError,
    LLMRequest,
    LLMResponse,
    LLMToolCall,
    LLMUsage,
)


@dataclass(frozen=True)
class NebiusSettings:
    api_key: str = ""
    base_url: str = "https://api.tokenfactory.nebius.com/v1"
    model: str = "nvidia/Nemotron-3_5-Lightning"
    timeout_seconds: float = 60
    max_retries: int = 2

    def validate(self) -> None:
        if not self.api_key.strip():
            raise LLMConfigurationError("NEBIUS_API_KEY is required when the LLM is used")
        if not self.base_url.startswith(("http://", "https://")):
            raise LLMConfigurationError("NEBIUS_BASE_URL must be an HTTP(S) URL")
        if not self.model.strip():
            raise LLMConfigurationError("NEBIUS_MODEL must not be empty")
        if self.timeout_seconds <= 0 or self.max_retries < 0:
            raise LLMConfigurationError("Nebius timeout and retries must be non-negative")


class NebiusLLMProvider:
    name = "nebius"

    def __init__(self, settings: NebiusSettings, client: Any | None = None) -> None:
        settings.validate()
        self.settings = settings
        self._client = client or OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
            max_retries=settings.max_retries,
        )

    def complete(self, request: LLMRequest) -> LLMResponse:
        messages = [message.model_dump(exclude_none=True) for message in request.messages]
        kwargs: dict[str, Any] = {
            "model": request.model or self.settings.model,
            "messages": messages,
            "temperature": request.generation.temperature,
        }
        if request.generation.max_tokens is not None:
            kwargs["max_tokens"] = request.generation.max_tokens
        if request.tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in request.tools
            ]
        if request.structured_output:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": request.structured_output.name,
                    "schema": request.structured_output.json_schema,
                    "strict": request.structured_output.strict,
                },
            }
        try:
            response = self._client.chat.completions.create(**kwargs)
        except (APITimeoutError, APIConnectionError, RateLimitError, APIError) as error:
            raise LLMProviderError("Nebius request failed") from error

        choice = response.choices[0]
        message = choice.message
        tool_calls = [
            LLMToolCall(
                id=call.id,
                name=call.function.name,
                arguments=_parse_arguments(call.function.arguments),
            )
            for call in (message.tool_calls or [])
        ]
        content = message.content
        structured = _parse_json(content) if request.structured_output and content else None
        usage = getattr(response, "usage", None)
        return LLMResponse(
            content=content,
            structured_content=structured,
            tool_calls=tool_calls,
            model=response.model,
            provider=self.name,
            request_id=getattr(response, "_request_id", None),
            usage=LLMUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", None),
                completion_tokens=getattr(usage, "completion_tokens", None),
                total_tokens=getattr(usage, "total_tokens", None),
            ) if usage else None,
        )


def _parse_json(value: str) -> dict[str, Any]:
    import json

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise LLMProviderError("Nebius returned malformed structured output") from error
    if not isinstance(parsed, dict):
        raise LLMProviderError("Nebius structured output must be an object")
    return parsed


def _parse_arguments(value: str) -> dict[str, Any]:
    return _parse_json(value)
