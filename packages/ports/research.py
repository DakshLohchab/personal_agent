"""Provider-neutral research contracts."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ResearchResult:
    url: str
    title: str | None = None
    publisher: str | None = None
    source_type: str | None = None
    snippet: str | None = None
    retrieved_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ResearchProvider(Protocol):
    name: str

    def search(self, query: str, max_results: int = 10) -> list[ResearchResult]: ...

