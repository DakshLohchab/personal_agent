from decimal import Decimal

from packages.ports.llm import LLMUsage
from services.evaluation.scoring import EvaluationResult, summarize
from services.observability.cost import ModelPricing, PricingCatalog


def test_evaluation_summary_is_deterministic() -> None:
    assert summarize([EvaluationResult("a", True), EvaluationResult("b", False)]) == {
        "case_count": 2,
        "passed_count": 1,
        "failure_count": 1,
        "pass_rate": 0.5,
    }


def test_unknown_pricing_is_explicitly_unavailable() -> None:
    estimate = PricingCatalog().estimate("unknown", "model", LLMUsage(prompt_tokens=10))
    assert estimate.amount is None


def test_pricing_uses_decimal_token_math() -> None:
    catalog = PricingCatalog(
        (ModelPricing("provider", "model", Decimal("1"), Decimal("2"), "v1"),)
    )
    estimate = catalog.estimate(
        "provider", "model", LLMUsage(prompt_tokens=1000, completion_tokens=500)
    )
    assert estimate.amount == Decimal("0.002")
