"""Application-level readiness evaluation, validation, and sanitization."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import Any

from packages.schemas.ai import DecisionInterpretation, MissingFieldPrompt
from packages.schemas.life_state import Constraint, LifeState
from packages.schemas.scenario import Scenario

RAW_ID_MAPPINGS: dict[str, str] = {
    "g_buffer": "Maintain an emergency cash buffer",
    "g_laptop": "Acquire a laptop for productivity or study",
    "g_trip": "Take a personal travel trip",
    "g_savings": "Grow liquid savings",
    "c_cash_floor": "Do not let available cash fall below emergency reserve",
    "c_budget": "Keep total spend within available budget",
    "c_minimum_cash": "Do not let cash balance fall below the minimum limit",
    "a_start_placeholder": "Simulation begins from current decision month",
    "a_nominal": "All values are in nominal currency without inflation adjustments",
}


def sanitize_identifier(text: str) -> str:
    """Replace raw schema identifiers with user-friendly descriptions."""
    stripped = text.strip()
    if stripped in RAW_ID_MAPPINGS:
        return RAW_ID_MAPPINGS[stripped]

    # Handle occurrences of known IDs within longer text
    for raw_id, clean_label in RAW_ID_MAPPINGS.items():
        if raw_id in text:
            text = text.replace(raw_id, clean_label)

    # Clean prefixed identifiers like g_emergency_fund or c_reserve
    match = re.match(r"^[gca]_([a-z0-9_]+)$", stripped)
    if match:
        words = match.group(1).replace("_", " ").strip()
        return words.capitalize()

    return text


def sanitize_identifiers_list(items: list[str]) -> list[str]:
    """Sanitize a list of strings, filtering pure placeholders and formatting IDs."""
    result: list[str] = []
    for item in items:
        cleaned = sanitize_identifier(item)
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def extract_amount(text: str, patterns: list[str]) -> Decimal | None:
    """Extract a decimal amount matching any of the regex patterns."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_val = match.group(1).replace(",", "").replace("k", "000").replace("K", "000")
            try:
                return Decimal(raw_val)
            except Exception:
                continue
    return None


def extract_integer(text: str, patterns: list[str]) -> int | None:
    """Extract an integer matching any of the regex patterns."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_val = match.group(1)
            try:
                return int(raw_val)
            except Exception:
                continue
    return None


def parse_provided_inputs(combined_text: str) -> dict[str, Any]:
    """Extract user-specified financial values from decision and context text."""
    # Starting cash
    cash = extract_amount(
        combined_text,
        [
            r"(?:have|savings|saved|capital|total\s+cash|funds)\s*(?:of|is|:)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*\b)",
            r"(?:₹|rs\.?|inr)\s*(\d[\d,]*\b)",
        ],
    )

    # Monthly essential expenses
    expenses = extract_amount(
        combined_text,
        [
            r"(?:monthly\s+)?(?:essential\s+)?(?:expenses|spending|spend|bills|outgoings)\s*(?:are|is|:|of)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*\b)",
            r"(?:spend|expense)\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*\b)\s*(?:per|a|\/)\s*month",
        ],
    )

    # Monthly income
    income = extract_amount(
        combined_text,
        [
            r"(?:monthly\s+)?(?:income|salary|take-?home|earn|earnings)\s*(?:is|are|:|of)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*\b)",
            r"(?:earn|income)\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*\b)\s*(?:per|a|\/)\s*month",
        ],
    )

    # Cash floor / emergency reserve
    cash_floor = extract_amount(
        combined_text,
        [
            r"(?:emergency\s+)?(?:reserve|buffer|floor|safety\s+net|untouched)\s*(?:is|are|:|of)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*\b)",
            r"keep\s*(?:at\s+least)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*\b)\s*(?:in\s+savings|untouched|as\s+buffer|as\s+reserve)",
        ],
    )

    # Horizon in months
    horizon = extract_integer(
        combined_text,
        [
            r"(?:horizon|model|simulate|duration|period)\s*(?:of|is|:)?\s*(\d+)\s*(?:months?|m\b)",
            r"(\d+)\s*months?\s*(?:horizon|duration|period|time)",
            r"(\d+)\s*months?\b",
            r"(\d+)\s*year[s]?\b",  # will handle below
        ],
    )
    if horizon is None:
        year_match = re.search(r"(\d+)\s*year[s]?\b", combined_text, re.IGNORECASE)
        if year_match:
            try:
                horizon = int(year_match.group(1)) * 12
            except Exception:
                pass

    # Option-specific costs: Laptop
    laptop_cost = extract_amount(
        combined_text,
        [
            r"laptop\s*(?:costs?|price|is|worth|budget|for|of)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*\b)",
            r"(?:cost\s+of\s+laptop|laptop\s+price)\s*(?:is|:)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*\b)",
        ],
    )

    # Option-specific costs: Trip
    trip_cost = extract_amount(
        combined_text,
        [
            r"(?:trip|travel|vacation)\s*(?:costs?|price|is|budget|for|of)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*\b)",
            r"(?:cost\s+of\s+trip|trip\s+price)\s*(?:is|:)?\s*(?:₹|rs\.?|inr)?\s*(\d[\d,]*\b)",
        ],
    )

    return {
        "cash": cash,
        "expenses": expenses,
        "income": income,
        "cash_floor": cash_floor,
        "horizon": horizon,
        "laptop_cost": laptop_cost,
        "trip_cost": trip_cost,
    }


def sanitize_and_validate_interpretation(
    interpretation: DecisionInterpretation,
    decision_text: str,
    context_text: str | None = None,
) -> DecisionInterpretation:
    """Deterministically enforce simulation readiness and strip placeholder values."""
    combined = f"{decision_text} {context_text or ''}"
    inputs = parse_provided_inputs(combined)

    # 1. Sanitize raw identifiers across all user-facing fields
    interpretation.goals = sanitize_identifiers_list(interpretation.goals)
    interpretation.constraints = sanitize_identifiers_list(interpretation.constraints)
    interpretation.commitments = sanitize_identifiers_list(interpretation.commitments)
    interpretation.proposed_assumptions = sanitize_identifiers_list(
        interpretation.proposed_assumptions
    )

    # Filter out fake assumptions that assert invented zero or full-amount values
    filtered_assumptions: list[str] = []
    for assump in interpretation.proposed_assumptions:
        low = assump.lower()
        if "monthly income is 0" in low or "expenses are 0" in low:
            continue
        if "horizon is 12" in low and inputs["horizon"] is None:
            continue
        filtered_assumptions.append(assump)
    interpretation.proposed_assumptions = filtered_assumptions

    # 2. Determine which candidate options involve spending
    has_laptop_option = any("laptop" in opt.name.lower() for opt in interpretation.candidate_options)
    has_trip_option = any("trip" in opt.name.lower() or "travel" in opt.name.lower() for opt in interpretation.candidate_options)

    # 3. Check for missing material fields
    missing_fields: list[str] = []
    missing_prompts: list[MissingFieldPrompt] = []

    if inputs["expenses"] is None:
        missing_fields.append("monthly_essential_expenses")
        missing_prompts.append(
            MissingFieldPrompt(
                key="monthly_essential_expenses",
                label="Monthly essential spending",
                question="What is your monthly essential spending?",
                field_type="currency",
                required=True,
            )
        )

    if has_laptop_option and inputs["laptop_cost"] is None:
        missing_fields.append("laptop_cost")
        missing_prompts.append(
            MissingFieldPrompt(
                key="laptop_cost",
                label="Laptop price",
                question="How much does the laptop cost?",
                field_type="currency",
                required=True,
            )
        )

    if has_trip_option and inputs["trip_cost"] is None:
        missing_fields.append("trip_cost")
        missing_prompts.append(
            MissingFieldPrompt(
                key="trip_cost",
                label="Trip cost",
                question="What will the trip cost?",
                field_type="currency",
                required=True,
            )
        )

    if inputs["cash_floor"] is None:
        missing_fields.append("cash_floor")
        missing_prompts.append(
            MissingFieldPrompt(
                key="cash_floor",
                label="Emergency cash reserve",
                question="How much emergency cash do you want untouched?",
                field_type="currency",
                required=True,
            )
        )

    if inputs["horizon"] is None:
        missing_fields.append("horizon_months")
        missing_prompts.append(
            MissingFieldPrompt(
                key="horizon_months",
                label="Time horizon (months)",
                question="How long should we model this decision (in months)?",
                field_type="integer",
                required=True,
            )
        )

    # 4. If material information is missing:
    if missing_fields:
        interpretation.simulation_readiness = "NEEDS_INFORMATION"
        interpretation.required_missing_fields = missing_fields
        interpretation.missing_field_prompts = missing_prompts

        # Strip any invented LifeState
        interpretation.current_state = None

        # Strip any invented scenario deltas (e.g. LLM assuming full ₹50,000 for laptop/trip)
        for opt in interpretation.candidate_options:
            opt.scenario = None

        # Ensure missing_information contains clear descriptions
        existing_missing = set(interpretation.missing_information)
        field_descriptions = {
            "monthly_essential_expenses": "Monthly essential spending (rent, bills, necessities)",
            "laptop_cost": "Estimated purchase price of the laptop",
            "trip_cost": "Estimated total cost of the trip",
            "cash_floor": "Minimum emergency cash buffer to protect untouched",
            "horizon_months": "Time horizon over which to model the outcomes",
        }
        for field in missing_fields:
            desc = field_descriptions.get(field, field)
            if not any(field in item.lower() or desc.lower() in item.lower() for item in existing_missing):
                interpretation.missing_information.append(desc)

        return interpretation

    # 5. If all required inputs ARE provided:
    interpretation.simulation_readiness = "READY_TO_SIMULATE"
    interpretation.required_missing_fields = []
    interpretation.missing_field_prompts = []

    # Build validated deterministic LifeState
    starting_cash = inputs["cash"] or Decimal("50000")
    essential_exp = inputs["expenses"] or Decimal("0")
    monthly_inc = inputs["income"] or Decimal("0")
    horizon_val = inputs["horizon"] or 12
    reserve_floor = inputs["cash_floor"] or Decimal("0")

    interpretation.current_state = LifeState(
        start_date=date.today(),
        horizon_months=min(max(horizon_val, 1), 120),
        cash=starting_cash,
        monthly_income=monthly_inc,
        monthly_essential_expenses=essential_exp,
        monthly_time_available_hours=Decimal("160"),
        goals=[],
        constraints=[
            Constraint(
                id="c_cash_floor",
                name="Do not let available cash fall below emergency reserve",
                metric="minimum_cash",
                limit=reserve_floor,
            )
        ]
        if reserve_floor > 0
        else [],
        commitments=[],
        variables=[],
    )

    # Assign deterministic scenario deltas for options
    for opt in interpretation.candidate_options:
        opt_low = opt.name.lower()
        if "laptop" in opt_low and inputs["laptop_cost"] is not None:
            opt.scenario = Scenario(
                id="buy-laptop",
                name=opt.name,
                deltas={"cash": -inputs["laptop_cost"]},
            )
        elif ("trip" in opt_low or "travel" in opt_low) and inputs["trip_cost"] is not None:
            opt.scenario = Scenario(
                id="take-trip",
                name=opt.name,
                deltas={"cash": -inputs["trip_cost"]},
            )
        elif "save" in opt_low:
            opt.scenario = Scenario(
                id="save-funds",
                name=opt.name,
                deltas={"cash": Decimal("0")},
            )

    return interpretation
