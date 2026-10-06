"""Token Harbor development adapter using its OpenAI-compatible API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    RateLimitError,
)

from packages.ports.llm import (
    LLMConfigurationError,
    LLMProviderError,
    LLMRequest,
    LLMResponse,
    LLMToolCall,
    LLMUsage,
)


@dataclass(frozen=True)
class TokenHarborSettings:
    api_key: str = ""
    base_url: str = "https://tokenharbor.ai/v1"
    model: str = "deepseek-v4.1-flash:free"
    timeout_seconds: float = 60
    max_retries: int = 2

    def validate(self) -> None:
        if not self.api_key.strip():
            raise LLMConfigurationError(
                "TOKENHARBOR_API_KEY is required when the Token Harbor provider is used"
            )
        if not self.base_url.startswith(("http://", "https://")):
            raise LLMConfigurationError("TOKENHARBOR_BASE_URL must be an HTTP(S) URL")
        if not self.model.strip():
            raise LLMConfigurationError("TOKENHARBOR_MODEL must not be empty")
        if self.timeout_seconds <= 0 or self.max_retries < 0:
            raise LLMConfigurationError(
                "Token Harbor timeout must be positive and retries must be non-negative"
            )


class TokenHarborLLMProvider:
    name = "token_harbor"

    def __init__(self, settings: TokenHarborSettings, client: Any | None = None) -> None:
        settings.validate()
        self.settings = settings
        self._client = client or OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
            max_retries=settings.max_retries,
        )

    def complete(self, request: LLMRequest) -> LLMResponse:
        started = perf_counter()
        kwargs: dict[str, Any] = {
            "model": request.model or self.settings.model,
            "messages": [message.model_dump(exclude_none=True) for message in request.messages],
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
        except APITimeoutError as error:
            raise LLMProviderError("Token Harbor request timed out") from error
        except (AuthenticationError, BadRequestError, NotFoundError) as error:
            raise LLMProviderError("Token Harbor rejected the request") from error
        except (APIConnectionError, RateLimitError, APIError) as error:
            raise LLMProviderError("Token Harbor request failed") from error

        try:
            choice = response.choices[0]
            message = choice.message
            tool_calls = [
                LLMToolCall(
                    id=call.id,
                    name=call.function.name,
                    arguments=_parse_json(call.function.arguments, "tool arguments"),
                )
                for call in (message.tool_calls or [])
            ]
        except (IndexError, AttributeError, TypeError) as error:
            raise LLMProviderError("Token Harbor returned a malformed response") from error

        content = message.content
        structured = (
            _parse_json(content, "structured output")
            if request.structured_output and content
            else None
        )
        usage = getattr(response, "usage", None)
        return LLMResponse(
            content=content,
            structured_content=structured,
            tool_calls=tool_calls,
            model=getattr(response, "model", request.model or self.settings.model),
            provider=self.name,
            request_id=getattr(response, "_request_id", None),
            usage=LLMUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", None),
                completion_tokens=getattr(usage, "completion_tokens", None),
                total_tokens=getattr(usage, "total_tokens", None),
            )
            if usage
            else None,
            metadata={
                "duration_ms": (perf_counter() - started) * 1000,
                "structured_output_requested": request.structured_output is not None,
                "tool_call_count": len(tool_calls),
                "retry_count": 0,
            },
        )


TokenHarborProvider = TokenHarborLLMProvider


def _parse_json(value: str | None, value_name: str) -> dict[str, Any]:
    if not isinstance(value, str):
        raise LLMProviderError(f"Token Harbor returned malformed {value_name}")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise LLMProviderError(f"Token Harbor returned malformed {value_name}") from error
    if not isinstance(parsed, dict):
        raise LLMProviderError(f"Token Harbor {value_name} must be an object")
    return parsed
