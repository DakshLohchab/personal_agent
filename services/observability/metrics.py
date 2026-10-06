"""Small local observability implementation with no vendor coupling."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from services.observability.context import get_correlation_id


@dataclass(frozen=True)
class Event:
    name: str
    status: str
    duration_ms: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None


class InMemoryObservability:
    """Testable local event sink; production exporters can implement the same shape."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def record(
        self,
        name: str,
        *,
        status: str,
        duration_ms: float | None = None,
        **attributes: Any,
    ) -> Event:
        event = Event(
            name=name,
            status=status,
            duration_ms=duration_ms,
            attributes=attributes,
            correlation_id=get_correlation_id(),
        )
        self.events.append(event)
        return event


class Timer:
    def __init__(self) -> None:
        self._started = perf_counter()

    @property
    def duration_ms(self) -> float:
        return (perf_counter() - self._started) * 1000
