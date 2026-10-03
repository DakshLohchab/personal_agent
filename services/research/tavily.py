"""Tavily adapter. No Tavily-specific details should escape this module."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from packages.ports.research import ResearchResult


class ResearchProviderError(RuntimeError):
    """A safe, provider-independent research failure."""


class TavilyResearchProvider:
    name = "tavily"

    def __init__(
        self, api_key: str, *, endpoint: str = "https://api.tavily.com/search", timeout: float = 15
    ) -> None:
        if not api_key:
            raise ValueError("Tavily API key is required")
        self._api_key = api_key
        self._endpoint = endpoint
        self._timeout = timeout

    def search(self, query: str, max_results: int = 10) -> list[ResearchResult]:
        if not query.strip():
            raise ValueError("query must not be empty")
        try:
            response = httpx.post(
                self._endpoint,
                json={"api_key": self._api_key, "query": query, "max_results": max_results},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload: Any = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ResearchProviderError("research provider request failed") from exc
        results = payload.get("results", []) if isinstance(payload, dict) else []
        if not isinstance(results, list):
            raise ResearchProviderError("research provider returned an invalid response")
        now = datetime.now(UTC)
        normalized: list[ResearchResult] = []
        for item in results[:max_results]:
            if not isinstance(item, dict) or not isinstance(item.get("url"), str):
                continue
            normalized.append(
                ResearchResult(
                    url=item["url"],
                    title=item.get("title"),
                    snippet=item.get("content"),
                    retrieved_at=now,
                    source_type="web",
                    metadata={"score": item.get("score")} if item.get("score") is not None else {},
                )
            )
        return normalized


class FakeResearchProvider:
    name = "fake"

    def __init__(self, results: list[ResearchResult] | None = None, error: Exception | None = None):
        self.results = results or []
        self.error = error

    def search(self, query: str, max_results: int = 10) -> list[ResearchResult]:
        if self.error is not None:
            raise self.error
        return self.results[:max_results]

