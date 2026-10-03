"""Provider-neutral embedding contracts."""

from typing import Protocol


class EmbeddingProvider(Protocol):
    model_name: str
    dimensions: int

    def embed_text(self, text: str) -> list[float]: ...

    def embed_many(self, texts: list[str]) -> list[list[float]]: ...


class FakeEmbeddingProvider:
    """Small deterministic provider for tests and local development."""

    def __init__(self, model_name: str = "fake", dimensions: int = 8) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        self.model_name = model_name
        self.dimensions = dimensions

    def embed_text(self, text: str) -> list[float]:
        values = [0.0] * self.dimensions
        for index, character in enumerate(text.encode("utf-8")):
            values[index % self.dimensions] += float(character)
        norm = sum(value * value for value in values) ** 0.5
        return [value / norm for value in values] if norm else values

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

