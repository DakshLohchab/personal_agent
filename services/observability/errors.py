"""Stable categories for operational and evaluation measurements."""

from __future__ import annotations

from enum import StrEnum


class ErrorCategory(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTH_ERROR = "AUTH_ERROR"
    RATE_LIMIT = "RATE_LIMIT"
    TIMEOUT = "TIMEOUT"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    TOOL_ERROR = "TOOL_ERROR"
    RESEARCH_ERROR = "RESEARCH_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    STRUCTURED_OUTPUT_ERROR = "STRUCTURED_OUTPUT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def categorize_error(error: BaseException) -> ErrorCategory:
    name = type(error).__name__.lower()
    message = str(error).lower()
    if "timeout" in name or "timed out" in message:
        return ErrorCategory.TIMEOUT
    if "validation" in name or "invalid" in name:
        return ErrorCategory.VALIDATION_ERROR
    if "rate" in name or "rate limit" in message:
        return ErrorCategory.RATE_LIMIT
    if "research" in name:
        return ErrorCategory.RESEARCH_ERROR
    if "memory" in name:
        return ErrorCategory.MEMORY_ERROR
    if "tool" in name:
        return ErrorCategory.TOOL_ERROR
    if "provider" in name or "llm" in name:
        return ErrorCategory.PROVIDER_ERROR
    return ErrorCategory.INTERNAL_ERROR
