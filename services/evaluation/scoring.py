"""Deterministic evaluation records and aggregate metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    input: dict[str, Any]
    expected: dict[str, Any]


@dataclass(frozen=True)
class EvaluationResult:
    case_name: str
    passed: bool
    diagnostics: dict[str, Any] = field(default_factory=dict)


def summarize(results: list[EvaluationResult]) -> dict[str, float | int]:
    passed = sum(result.passed for result in results)
    total = len(results)
    return {
        "case_count": total,
        "passed_count": passed,
        "failure_count": total - passed,
        "pass_rate": passed / total if total else 0.0,
    }
