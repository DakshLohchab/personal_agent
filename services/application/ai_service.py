"""Application orchestration for structured decision interpretation."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from packages.ports.llm import (
    LLMMessage,
    LLMProvider,
    LLMRequest,
    LLMStructuredOutput,
    LLMToolDefinition,
)
from packages.schemas.ai import AIExplanation, DecisionInterpretation
from services.application.ai_tools import DeterministicToolRegistry
from services.application.prompts import (
    DECISION_INTERPRETATION_PROMPT,
    FINAL_EXPLANATION_PROMPT,
    PROMPT_VERSION,
    TOOL_USE_PROMPT,
)


class AIServiceError(ValueError):
    """The provider returned output that cannot be used by the application."""


class AIService:
    def __init__(
        self,
        provider: LLMProvider,
        tools: DeterministicToolRegistry | None = None,
    ) -> None:
        self.provider = provider
        self.tools = tools or DeterministicToolRegistry()

    def interpret(self, decision: str, *, model: str, context: str | None = None) -> dict[str, Any]:
        user_content = decision if not context else f"{decision}\n\nUser context:\n{context}"
        request = LLMRequest(
            model=model,
            messages=[
                LLMMessage(role="system", content=DECISION_INTERPRETATION_PROMPT),
                LLMMessage(role="user", content=user_content),
            ],
            structured_output=LLMStructuredOutput(
                name="decision_interpretation",
                json_schema=DecisionInterpretation.model_json_schema(),
            ),
            tools=[
                LLMToolDefinition(
                    name=item["name"],
                    description=item["description"],
                    parameters=item["parameters"],
                )
                for item in self.tools.definitions()
            ],
        )
        response = self.provider.complete(request)
        interpretation = self._interpretation(response.structured_content)
        tool_results: list[dict[str, Any]] = []
        for call in response.tool_calls:
            try:
                result = self.tools.execute(call.name, call.arguments)
            except ValueError as error:
                raise AIServiceError(str(error)) from error
            tool_results.append(
                {
                    "tool_call_id": call.id,
                    "name": call.name,
                    "result": result.model_dump(mode="json")
                    if hasattr(result, "model_dump")
                    else result,
                }
            )

        explanation = self._explain(decision, interpretation, tool_results, model)
        return {
            "interpretation": interpretation,
            "tool_results": tool_results,
            "explanation": explanation,
            "metadata": {
                "prompt_version": PROMPT_VERSION,
                "provider": response.provider,
                "model": response.model,
                "request_id": response.request_id,
                "usage": response.usage.model_dump() if response.usage else None,
            },
        }

    @staticmethod
    def _interpretation(value: dict[str, Any] | None) -> DecisionInterpretation:
        if value is None:
            raise AIServiceError("provider did not return structured decision interpretation")
        try:
            return DecisionInterpretation.model_validate(value)
        except ValidationError as error:
            raise AIServiceError("provider returned invalid decision interpretation") from error

    def _explain(
        self,
        decision: str,
        interpretation: DecisionInterpretation,
        tool_results: list[dict[str, Any]],
        model: str,
    ) -> AIExplanation:
        request = LLMRequest(
            model=model,
            messages=[
                LLMMessage(
                    role="system",
                    content=f"{FINAL_EXPLANATION_PROMPT}\n{TOOL_USE_PROMPT}",
                ),
                LLMMessage(
                    role="user",
                    content=str(
                        {
                            "decision": decision,
                            "interpretation": interpretation.model_dump(mode="json"),
                            "deterministic_tool_results": tool_results,
                        }
                    ),
                ),
            ],
            structured_output=LLMStructuredOutput(
                name="decision_explanation",
                json_schema=AIExplanation.model_json_schema(),
            ),
        )
        response = self.provider.complete(request)
        if response.structured_content is None:
            raise AIServiceError("provider did not return structured explanation")
        try:
            return AIExplanation.model_validate(response.structured_content)
        except ValidationError as error:
            raise AIServiceError("provider returned invalid explanation") from error
