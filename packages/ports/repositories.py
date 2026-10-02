"""Persistence interfaces used by application code without ORM leakage."""

from typing import Any, Mapping, Protocol
from uuid import UUID

from packages.ports.auth import AuthPrincipal

Record = Mapping[str, Any]
RecordValues = Mapping[str, Any]


class UserOwnedRepository(Protocol):
    def create(self, user_id: UUID, values: RecordValues) -> Record: ...

    def get(self, user_id: UUID, record_id: UUID) -> Record | None: ...

    def list_for_user(self, user_id: UUID) -> list[Record]: ...

    def update(self, user_id: UUID, record_id: UUID, values: RecordValues) -> Record | None: ...

    def delete(self, user_id: UUID, record_id: UUID) -> bool: ...


class ProfileRepository(Protocol):
    def create(
        self,
        principal: AuthPrincipal,
        *,
        display_name: str | None = None,
        timezone: str | None = None,
    ) -> Record: ...

    def get(self, user_id: UUID) -> Record | None: ...

    def delete(self, user_id: UUID) -> bool: ...


class GoalRepository(UserOwnedRepository, Protocol): ...


class ConstraintRepository(UserOwnedRepository, Protocol): ...


class CommitmentRepository(UserOwnedRepository, Protocol): ...


class ScenarioRepository(UserOwnedRepository, Protocol):
    def add_version(
        self,
        user_id: UUID,
        scenario_id: UUID,
        state_snapshot: RecordValues,
        scenario_snapshot: RecordValues,
        *,
        version_number: int | None = None,
    ) -> Record: ...

    def get_version(
        self, user_id: UUID, scenario_id: UUID, version_id: UUID
    ) -> Record | None: ...

    def create_branch(
        self,
        user_id: UUID,
        scenario_id: UUID,
        scenario_version_id: UUID,
        name: str,
        deltas: RecordValues,
        *,
        parent_branch_id: UUID | None = None,
    ) -> Record: ...

    def list_branches(self, user_id: UUID, scenario_id: UUID) -> list[Record]: ...


class AssumptionRepository(UserOwnedRepository, Protocol): ...


class ResearchRepository(Protocol):
    def create_query(self, user_id: UUID, values: RecordValues) -> Record: ...

    def get_query(self, user_id: UUID, query_id: UUID) -> Record | None: ...

    def list_queries(self, user_id: UUID) -> list[Record]: ...

    def create_source(
        self, user_id: UUID, research_query_id: UUID, values: RecordValues
    ) -> Record: ...

    def list_sources(self, user_id: UUID, research_query_id: UUID) -> list[Record]: ...


class EvidenceRepository(UserOwnedRepository, Protocol): ...


class RunRepository(UserOwnedRepository, Protocol): ...


class MemoryRepository(UserOwnedRepository, Protocol): ...


class FileRepository(UserOwnedRepository, Protocol): ...


class DocumentRepository(UserOwnedRepository, Protocol):
    def create_chunk(self, user_id: UUID, document_id: UUID, values: RecordValues) -> Record: ...

    def list_chunks(self, user_id: UUID, document_id: UUID) -> list[Record]: ...


class EmbeddingRepository(Protocol):
    def create(self, user_id: UUID, values: RecordValues) -> Record: ...

    def exact_cosine_search(
        self, user_id: UUID, vector: list[float], *, limit: int = 10
    ) -> list[Record]: ...


class UnitOfWork(Protocol):
    profiles: ProfileRepository
    goals: GoalRepository
    constraints: ConstraintRepository
    commitments: CommitmentRepository
    scenarios: ScenarioRepository
    assumptions: AssumptionRepository
    research: ResearchRepository
    evidence: EvidenceRepository
    runs: RunRepository
    memories: MemoryRepository
    files: FileRepository
    documents: DocumentRepository
    embeddings: EmbeddingRepository

    def begin(self) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...