from types import SimpleNamespace

import pytest

from packages.ports.llm import (
    LLMConfigurationError,
    LLMProviderError,
    LLMRequest,
    LLMStructuredOutput,
)
from services.llm.token_harbor import TokenHarborLLMProvider, TokenHarborSettings


def test_token_harbor_requires_key_only_when_constructed() -> None:
    with pytest.raises(LLMConfigurationError):
        TokenHarborLLMProvider(TokenHarborSettings())


def test_token_harbor_maps_structured_output_and_tool_calls() -> None:
    class FakeCompletions:
        def create(self, **kwargs: object) -> object:
            assert kwargs["model"] == "deepseek-test"
            assert "response_format" in kwargs
            assert "tools" in kwargs
            return SimpleNamespace(
                model="deepseek-test",
                _request_id="req-1",
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"ok": true}',
                            tool_calls=[
                                SimpleNamespace(
                                    id="call-1",
                                    function=SimpleNamespace(
                                        name="simulate_scenario",
                                        arguments='{"seed": 42}',
                                    ),
                                )
                            ],
                        )
                    )
                ],
                usage=SimpleNamespace(prompt_tokens=1, completion_tokens=2, total_tokens=3),
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    provider = TokenHarborLLMProvider(
        TokenHarborSettings(api_key="test", model="deepseek-test"),
        client=client,
    )
    response = provider.complete(
        LLMRequest(
            model="deepseek-test",
            messages=[{"role": "user", "content": "hello"}],
            structured_output=LLMStructuredOutput(name="test", json_schema={"type": "object"}),
            tools=[
                {
                    "name": "simulate_scenario",
                    "description": "simulate",
                    "parameters": {"type": "object"},
                }
            ],
        )
    )
    assert response.provider == "token_harbor"
    assert response.structured_content == {"ok": True}
    assert response.tool_calls[0].arguments == {"seed": 42}


def test_token_harbor_rejects_malformed_structured_output() -> None:
    class FakeCompletions:
        def create(self, **_: object) -> object:
            return SimpleNamespace(
                model="deepseek-test",
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="not-json", tool_calls=[])
                    )
                ],
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    provider = TokenHarborLLMProvider(TokenHarborSettings(api_key="test"), client=client)
    with pytest.raises(LLMProviderError, match="malformed structured output"):
        provider.complete(
            LLMRequest(
                model="deepseek-test",
                messages=[{"role": "user", "content": "hello"}],
                structured_output=LLMStructuredOutput(
                    name="test", json_schema={"type": "object"}
                ),
            )
        )
