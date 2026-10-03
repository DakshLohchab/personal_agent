"""Research orchestration and bounded source persistence."""

from __future__ import annotations

from hashlib import sha256
from typing import Any
from uuid import UUID

from packages.ports.research import ResearchProvider, ResearchResult


class ResearchService:
    def __init__(self, provider: ResearchProvider, research_repository: Any) -> None:
        self.provider = provider
        self.research_repository = research_repository

    def search(self, user_id: UUID, query: str, max_results: int = 10) -> dict[str, Any]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= max_results <= 50:
            raise ValueError("max_results must be between 1 and 50")
        results = self.provider.search(query, max_results)
        query_record = self.research_repository.create_query(
            user_id, {"query": query, "provider": self.provider.name}
        )
        sources = [
            self.research_repository.create_source(
                user_id,
                query_record["id"],
                self._source_values(result),
            )
            for result in results
            if result.url.strip()
        ]
        return {"research_query_id": query_record["id"], "sources": sources}

    @staticmethod
    def _source_values(result: ResearchResult) -> dict[str, Any]:
        snippet = (result.snippet or "")[:2000]
        return {
            "url": result.url,
            "title": result.title,
            "publisher": result.publisher,
            "source_type": result.source_type or "web",
            "retrieved_at": result.retrieved_at,
            "snippet": snippet,
            "content_hash": sha256(snippet.encode("utf-8")).hexdigest() if snippet else None,
            "metadata_json": dict(result.metadata),
        }

