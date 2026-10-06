"""Deterministic, explicitly estimated LLM cost calculation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from packages.ports.llm import LLMUsage


@dataclass(frozen=True)
class ModelPricing:
    provider: str
    model: str
    input_per_million: Decimal
    output_per_million: Decimal
    version: str = "unknown"


@dataclass(frozen=True)
class CostEstimate:
    amount: Decimal | None
    currency: str = "USD"
    pricing_version: str | None = None


class PricingCatalog:
    def __init__(self, prices: tuple[ModelPricing, ...] = ()) -> None:
        self._prices = {(item.provider, item.model): item for item in prices}

    def lookup(self, provider: str, model: str) -> ModelPricing | None:
        return self._prices.get((provider, model))

    def estimate(self, provider: str, model: str, usage: LLMUsage | None) -> CostEstimate:
        pricing = self.lookup(provider, model)
        if pricing is None or usage is None:
            return CostEstimate(amount=None)
        input_tokens = usage.prompt_tokens or 0
        output_tokens = usage.completion_tokens or 0
        amount = (
            Decimal(input_tokens) * pricing.input_per_million
            + Decimal(output_tokens) * pricing.output_per_million
        ) / Decimal(1_000_000)
        return CostEstimate(amount=amount, pricing_version=pricing.version)
