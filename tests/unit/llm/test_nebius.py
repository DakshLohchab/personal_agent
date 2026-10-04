from types import SimpleNamespace

import pytest

from packages.ports.llm import LLMConfigurationError, LLMRequest, LLMStructuredOutput
from services.llm.nebius import NebiusLLMProvider, NebiusSettings


def test_nebius_requires_key_only_when_constructed() -> None:
    with pytest.raises(LLMConfigurationError):
        NebiusLLMProvider(NebiusSettings())


def test_nebius_maps_openai_compatible_response() -> None:
    class FakeCompletions:
        def create(self, **_: object) -> object:
            return SimpleNamespace(
                model="nvidia/Nemotron-3_5-Lightning",
                _request_id="req-1",
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content='{"ok": true}', tool_calls=[])
                    )
                ],
                usage=SimpleNamespace(prompt_tokens=1, completion_tokens=2, total_tokens=3),
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    provider = NebiusLLMProvider(NebiusSettings(api_key="test"), client=client)
    response = provider.complete(
        LLMRequest(
            model="nvidia/Nemotron-3_5-Lightning",
            messages=[{"role": "user", "content": "hello"}],
            structured_output=LLMStructuredOutput(name="test", json_schema={"type": "object"}),
        )
    )
    assert response.structured_content == {"ok": True}
    assert response.request_id == "req-1"
    assert response.usage is not None
