"""Small job boundary for immediate and background agent runs."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Generic, Protocol, TypeVar
from uuid import UUID, uuid4

T = TypeVar("T")


class JobQueue(Protocol, Generic[T]):
    def submit(self, task: Callable[[], T]) -> UUID: ...
    def status(self, job_id: UUID) -> str: ...
    def result(self, job_id: UUID) -> T: ...


@dataclass
class LocalJobQueue(Generic[T]):
    _executor: ThreadPoolExecutor | None = None

    def __post_init__(self) -> None:
        self._executor = self._executor or ThreadPoolExecutor(max_workers=4)
        self._jobs: dict[UUID, Future[T]] = {}

    def submit(self, task: Callable[[], T]) -> UUID:
        job_id = uuid4()
        executor = self._executor
        if executor is None:
            raise RuntimeError("job queue is not initialized")
        self._jobs[job_id] = executor.submit(task)
        return job_id

    def status(self, job_id: UUID) -> str:
        future = self._jobs.get(job_id)
        if future is None:
            return "unknown"
        if not future.done():
            return "running"
        return "failed" if future.exception() is not None else "completed"

    def result(self, job_id: UUID) -> T:
        future = self._jobs.get(job_id)
        if future is None:
            raise KeyError(f"unknown job: {job_id}")
        return future.result()


class QStashJobQueue(Generic[T]):
    """Adapter boundary; transport integration is injected by the host."""

    def __init__(self, publisher: Callable[[str], str]) -> None:
        self.publisher = publisher
        self._statuses: dict[UUID, str] = {}

    def submit(self, task: Callable[[], T]) -> UUID:
        del task
        raise NotImplementedError("QStash requires a serializable application callback")

    def status(self, job_id: UUID) -> str:
        return self._statuses.get(job_id, "unknown")

    def result(self, job_id: UUID) -> T:
        del job_id
        raise RuntimeError("QStash results are delivered through the application callback")
