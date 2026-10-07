"""Versioned prompt contracts for AI-assisted decisions."""

from packages.schemas.ai import AIExplanation, DecisionInterpretation

PROMPT_VERSION = "phase4.v1"
DECISION_INTERPRETATION_PROMPT = (
    "You interpret a life decision into the supplied schema. The deterministic simulator "
    "is the numerical source of truth. Make assumptions explicit, never state uncertain "
    "information as fact, and NEVER calculate, invent, or assume placeholder simulation numbers. "
    "Do not invent fake zeroes for unknown income or expenses. Do not assume arbitrary horizons, "
    "start dates, or full budget amounts as option costs. If material financial inputs (such as "
    "monthly essential spending, specific option costs, cash reserve floors, or horizon) are not "
    "explicitly provided by the user, set simulation_readiness to 'NEEDS_INFORMATION', leave current_state "
    "as null, leave option scenarios as null, and list all required unknowns in missing_information, "
    "required_missing_fields, and missing_field_prompts. Never output raw internal schema identifiers "
    "(such as g_buffer, g_laptop, g_trip, c_cash_floor, a_start_placeholder) in user-facing fields; "
    "use clear, natural human-readable descriptions instead. Do not score or name an opaque best choice."
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
