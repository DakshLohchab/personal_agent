"""SQLAlchemy persistence schema; migrations remain the DDL source of truth."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UUIDPrimaryKey:
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)


class TimestampColumns:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class UserOwnedColumns:
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )


class ProfileModel(UUIDPrimaryKey, TimestampColumns, Base):
    __tablename__ = "profiles"

    auth_subject: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    auth_provider: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str | None] = mapped_column(Text)


class GoalModel(UUIDPrimaryKey, UserOwnedColumns, TimestampColumns, Base):
    __tablename__ = "goals"
    __table_args__ = (Index("ix_goals_user_id", "user_id"),)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    target_value: Mapped[Decimal | None] = mapped_column(Numeric)
    current_value: Mapped[Decimal | None] = mapped_column(Numeric)
    unit: Mapped[str | None] = mapped_column(Text)


class ConstraintModel(UUIDPrimaryKey, UserOwnedColumns, TimestampColumns, Base):
    __tablename__ = "constraints"
    __table_args__ = (Index("ix_constraints_user_id", "user_id"),)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    metric: Mapped[str] = mapped_column(Text, nullable=False)
    limit_value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)


class CommitmentModel(UUIDPrimaryKey, UserOwnedColumns, TimestampColumns, Base):
    __tablename__ = "commitments"
    __table_args__ = (
        Index("ix_commitments_user_id", "user_id"),
        CheckConstraint("monthly_cost >= 0", name="ck_commitments_monthly_cost_nonnegative"),
        CheckConstraint("monthly_hours >= 0", name="ck_commitments_monthly_hours_nonnegative"),
        CheckConstraint(
            "end_month IS NULL OR end_month >= start_month",
            name="ck_commitments_month_range",
        ),
        CheckConstraint("start_month >= 1", name="ck_commitments_start_month_positive"),
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    monthly_cost: Mapped[Decimal] = mapped_column(Numeric, nullable=False, server_default="0")
    monthly_hours: Mapped[Decimal] = mapped_column(Numeric, nullable=False, server_default="0")
    start_month: Mapped[int] = mapped_column(Integer, nullable=False)
    end_month: Mapped[int | None] = mapped_column(Integer)


class ScenarioModel(UUIDPrimaryKey, UserOwnedColumns, TimestampColumns, Base):
    __tablename__ = "scenarios"
    __table_args__ = (Index("ix_scenarios_user_id", "user_id"),)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class ScenarioVersionModel(UUIDPrimaryKey, Base):
    __tablename__ = "scenario_versions"
    __table_args__ = (
        UniqueConstraint("scenario_id", "version_number", name="uq_scenario_versions_number"),
        Index("ix_scenario_versions_scenario_id", "scenario_id"),
        CheckConstraint("version_number > 0", name="ck_scenario_versions_number_positive"),
    )

    scenario_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    scenario_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ScenarioBranchModel(UUIDPrimaryKey, Base):
    __tablename__ = "scenario_branches"
    __table_args__ = (
        Index("ix_scenario_branches_scenario_id", "scenario_id"),
        Index("ix_scenario_branches_parent_branch_id", "parent_branch_id"),
    )

    scenario_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    parent_branch_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scenario_branches.id", ondelete="CASCADE")
    )
    scenario_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scenario_versions.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    deltas: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AssumptionModel(UUIDPrimaryKey, UserOwnedColumns, TimestampColumns, Base):
    __tablename__ = "assumptions"
    __table_args__ = (
        Index("ix_assumptions_user_id", "user_id"),
        Index("ix_assumptions_scenario_id", "scenario_id"),
        CheckConstraint(
            "source_type <> 'research' OR evidence_id IS NOT NULL",
            name="ck_assumptions_research_requires_evidence",
        ),
    )

    scenario_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE")
    )
    key: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    unit: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("evidence.id", ondelete="RESTRICT")
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="active")


class ResearchQueryModel(UUIDPrimaryKey, UserOwnedColumns, Base):
    __tablename__ = "research_queries"
    __table_args__ = (Index("ix_research_queries_user_id", "user_id"),)

    query: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ResearchSourceModel(UUIDPrimaryKey, Base):
    __tablename__ = "research_sources"
    __table_args__ = (
        UniqueConstraint("research_query_id", "url", name="uq_research_sources_query_url"),
        Index("ix_research_sources_research_query_id", "research_query_id"),
    )

    research_query_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("research_queries.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    publisher: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EvidenceModel(UUIDPrimaryKey, UserOwnedColumns, Base):
    __tablename__ = "evidence"
    __table_args__ = (Index("ix_evidence_user_id", "user_id"),)

    research_source_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("research_sources.id", ondelete="SET NULL")
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RunModel(UUIDPrimaryKey, UserOwnedColumns, Base):
    __tablename__ = "runs"
    __table_args__ = (
        Index("ix_runs_user_id", "user_id"),
        Index("ix_runs_scenario_id", "scenario_id"),
        Index("ix_runs_created_at", "created_at"),
    )

    scenario_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scenarios.id", ondelete="SET NULL")
    )
    engine_version: Mapped[str] = mapped_column(Text, nullable=False)
    schema_version: Mapped[str] = mapped_column(Text, nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    result_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AgentRunModel(UUIDPrimaryKey, UserOwnedColumns, Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_user_id", "user_id"),
        Index("ix_agent_runs_run_id", "run_id"),
    )

    run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False
    )
    parent_run_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    agent_version: Mapped[str] = mapped_column(Text, nullable=False)
    model_identifier: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input_hash: Mapped[str] = mapped_column(Text, nullable=False)
    output_hash: Mapped[str | None] = mapped_column(Text)
    error_category: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    tool_calls: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    output_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )


class MemoryModel(UUIDPrimaryKey, UserOwnedColumns, TimestampColumns, Base):
    __tablename__ = "memories"
    __table_args__ = (
        Index("ix_memories_user_id", "user_id"),
        Index("ix_memories_user_status", "user_id", "status"),
        Index("ix_memories_user_memory_type", "user_id", "memory_type"),
    )

    memory_type: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )
    provenance_type: Mapped[str | None] = mapped_column(Text)
    provenance_ref: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="active")
    retention_policy: Mapped[str] = mapped_column(Text, nullable=False, server_default="persistent")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EmbeddingModel(UUIDPrimaryKey, UserOwnedColumns, Base):
    __tablename__ = "embeddings"
    __table_args__ = (
        Index("ix_embeddings_user_id", "user_id"),
        CheckConstraint("dimensions > 0", name="ck_embeddings_dimensions_positive"),
        CheckConstraint(
            "num_nonnulls(memory_id, document_chunk_id, evidence_id) = 1",
            name="ck_embeddings_exactly_one_owner",
        ),
    )

    memory_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE")
    )
    document_chunk_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("document_chunks.id", ondelete="CASCADE")
    )
    evidence_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("evidence.id", ondelete="CASCADE")
    )
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(dim=None))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FileModel(UUIDPrimaryKey, UserOwnedColumns, TimestampColumns, Base):
    __tablename__ = "files"
    __table_args__ = (
        Index("ix_files_user_id", "user_id"),
        Index("ix_files_user_status", "user_id", "status"),
        UniqueConstraint("object_key", name="uq_files_object_key"),
    )

    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str | None] = mapped_column(Text)
    storage_provider: Mapped[str] = mapped_column(Text, nullable=False, server_default="r2")
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    extraction_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="not_started"
    )
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    # Legacy columns remain during the Phase 3A compatibility window.
    original_name: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )


class DocumentModel(UUIDPrimaryKey, UserOwnedColumns, TimestampColumns, Base):
    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_user_id", "user_id"),)

    file_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    document_type: Mapped[str] = mapped_column(Text, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer)
    text_status: Mapped[str] = mapped_column(Text, nullable=False, server_default="not_started")
    # Legacy columns remain during the Phase 3A compatibility window.
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )


class DocumentChunkModel(UUIDPrimaryKey, UserOwnedColumns, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_index"),
        Index("ix_document_chunks_user_id", "user_id"),
        Index("ix_document_chunks_document_id", "document_id"),
        CheckConstraint("chunk_index >= 0", name="ck_document_chunks_index_nonnegative"),
    )

    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    # Legacy columns remain during the Phase 3A compatibility window.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
