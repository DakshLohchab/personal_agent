"""Versioned prompt contracts for AI-assisted decisions."""

from packages.schemas.ai import AIExplanation, DecisionInterpretation

PROMPT_VERSION = "phase4.v1"
DECISION_INTERPRETATION_PROMPT = (
    "You interpret a life decision into the supplied schema. The deterministic simulator "
    "is the numerical source of truth. Make assumptions explicit, never state uncertain "
    "information as fact, and do not calculate or invent simulation numbers. Do not score "
    "or name an opaque best choice."
)
TOOL_USE_PROMPT = (
    "Use an allowlisted deterministic tool when numerical analysis is needed. Tool results "
    "are authoritative and must not be replaced with invented numbers."
)
FINAL_EXPLANATION_PROMPT = (
    "Explain the structured interpretation and returned deterministic tool results. The "
    "simulator owns all numerical truth; distinguish assumptions from user facts and include "
    "caveats. Do not produce an opaque best-choice score."
)


def schema_for(model: type[DecisionInterpretation | AIExplanation]) -> dict:
    return model.model_json_schema()
