"""Correlation context shared by request, run, agent, and tool boundaries."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator
from uuid import UUID, uuid4

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def set_correlation_id(value: UUID | str | None = None) -> str:
    identifier = str(value or uuid4())
    _correlation_id.set(identifier)
    return identifier


@contextmanager
def correlation_id(value: UUID | str | None = None) -> Iterator[str]:
    token = _correlation_id.set(str(value or uuid4()))
    try:
        yield _correlation_id.get() or ""
    finally:
        _correlation_id.reset(token)
