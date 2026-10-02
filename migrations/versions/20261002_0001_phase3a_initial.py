"""Initial Phase 3A persistence schema.

Revision ID: 20261002_0001
Revises:
Create Date: 2026-10-02
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20261002_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE profiles (
            id uuid PRIMARY KEY,
            auth_subject text NOT NULL UNIQUE,
            auth_provider text NOT NULL,
            display_name text,
            timezone text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE TABLE goals (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            name text NOT NULL,
            target_value numeric,
            current_value numeric,
            unit text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_goals_user_id ON goals(user_id);
        CREATE TABLE constraints (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            name text NOT NULL,
            metric text NOT NULL,
            limit_value numeric NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_constraints_user_id ON constraints(user_id);
        CREATE TABLE commitments (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            name text NOT NULL,
            monthly_cost numeric NOT NULL DEFAULT 0 CHECK (monthly_cost >= 0),
            monthly_hours numeric NOT NULL DEFAULT 0 CHECK (monthly_hours >= 0),
            start_month integer NOT NULL CONSTRAINT ck_commitments_start_month_positive CHECK (start_month >= 1),
            end_month integer,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CHECK (end_month IS NULL OR end_month >= start_month)
        );
        CREATE INDEX ix_commitments_user_id ON commitments(user_id);
        CREATE TABLE scenarios (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            name text NOT NULL,
            description text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_scenarios_user_id ON scenarios(user_id);
        CREATE TABLE scenario_versions (
            id uuid PRIMARY KEY,
            scenario_id uuid NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
            version_number integer NOT NULL CONSTRAINT ck_scenario_versions_number_positive CHECK (version_number > 0),
            state_snapshot jsonb NOT NULL,
            scenario_snapshot jsonb NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_scenario_versions_number UNIQUE (scenario_id, version_number)
        );
        CREATE INDEX ix_scenario_versions_scenario_id ON scenario_versions(scenario_id);
        CREATE TABLE scenario_branches (
            id uuid PRIMARY KEY,
            scenario_id uuid NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
            parent_branch_id uuid REFERENCES scenario_branches(id) ON DELETE CASCADE,
            scenario_version_id uuid NOT NULL REFERENCES scenario_versions(id) ON DELETE RESTRICT,
            name text NOT NULL,
            deltas jsonb NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_scenario_branches_scenario_id ON scenario_branches(scenario_id);
        CREATE INDEX ix_scenario_branches_parent_branch_id ON scenario_branches(parent_branch_id);
        CREATE TABLE research_queries (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            query text NOT NULL,
            provider text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_research_queries_user_id ON research_queries(user_id);
        CREATE TABLE research_sources (
            id uuid PRIMARY KEY,
            research_query_id uuid NOT NULL REFERENCES research_queries(id) ON DELETE CASCADE,
            url text NOT NULL,
            title text,
            publisher text,
            source_type text,
            retrieved_at timestamptz NOT NULL,
            content_hash text,
            snippet text,
            metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_research_sources_query_url UNIQUE (research_query_id, url)
        );
        CREATE INDEX ix_research_sources_research_query_id ON research_sources(research_query_id);
        CREATE TABLE evidence (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            research_source_id uuid REFERENCES research_sources(id) ON DELETE SET NULL,
            claim_text text NOT NULL,
            evidence_text text NOT NULL,
            source_url text,
            content_hash text,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_evidence_user_id ON evidence(user_id);
        CREATE TABLE assumptions (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            scenario_id uuid REFERENCES scenarios(id) ON DELETE CASCADE,
            key text NOT NULL,
            value jsonb NOT NULL,
            unit text,
            source_type text NOT NULL,
            evidence_id uuid REFERENCES evidence(id) ON DELETE RESTRICT,
            confidence numeric,
            status text NOT NULL DEFAULT 'active',
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_assumptions_research_requires_evidence
                CHECK (source_type <> 'research' OR evidence_id IS NOT NULL)
        );
        CREATE INDEX ix_assumptions_user_id ON assumptions(user_id);
        CREATE INDEX ix_assumptions_scenario_id ON assumptions(scenario_id);
        CREATE TABLE runs (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            scenario_id uuid REFERENCES scenarios(id) ON DELETE SET NULL,
            engine_version text NOT NULL,
            schema_version text NOT NULL,
            seed integer,
            input_snapshot jsonb NOT NULL,
            result_snapshot jsonb NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_runs_user_id ON runs(user_id);
        CREATE INDEX ix_runs_scenario_id ON runs(scenario_id);
        CREATE INDEX ix_runs_created_at ON runs(created_at);
        CREATE TABLE memories (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            memory_type text NOT NULL,
            content text NOT NULL,
            structured_data jsonb NOT NULL DEFAULT '{}'::jsonb,
            provenance_type text,
            provenance_ref text,
            confidence numeric,
            status text NOT NULL DEFAULT 'active',
            retention_policy text NOT NULL DEFAULT 'persistent',
            expires_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_memories_user_id ON memories(user_id);
        CREATE INDEX ix_memories_user_status ON memories(user_id, status);
        CREATE INDEX ix_memories_user_memory_type ON memories(user_id, memory_type);
        CREATE TABLE files (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            original_name text NOT NULL,
            media_type text,
            size_bytes integer,
            content_hash text,
            metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_files_user_id ON files(user_id);
        CREATE TABLE documents (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            file_id uuid REFERENCES files(id) ON DELETE SET NULL,
            title text NOT NULL,
            content text NOT NULL,
            content_hash text,
            metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_documents_user_id ON documents(user_id);
        CREATE TABLE document_chunks (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index integer NOT NULL CONSTRAINT ck_document_chunks_index_nonnegative CHECK (chunk_index >= 0),
            content text NOT NULL,
            metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_document_chunks_index UNIQUE (document_id, chunk_index)
        );
        CREATE INDEX ix_document_chunks_user_id ON document_chunks(user_id);
        CREATE INDEX ix_document_chunks_document_id ON document_chunks(document_id);
        CREATE TABLE embeddings (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            memory_id uuid REFERENCES memories(id) ON DELETE CASCADE,
            document_chunk_id uuid REFERENCES document_chunks(id) ON DELETE CASCADE,
            evidence_id uuid REFERENCES evidence(id) ON DELETE CASCADE,
            model_name text NOT NULL,
            dimensions integer NOT NULL CHECK (dimensions > 0),
            embedding vector,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_embeddings_exactly_one_owner
                CHECK (num_nonnulls(memory_id, document_chunk_id, evidence_id) = 1)
        );
        CREATE INDEX ix_embeddings_user_id ON embeddings(user_id);
        """
    )
    _enable_rls()


def _enable_rls() -> None:
    user_tables = (
        "goals",
        "constraints",
        "commitments",
        "scenarios",
        "assumptions",
        "research_queries",
        "evidence",
        "runs",
        "memories",
        "files",
        "documents",
        "document_chunks",
        "embeddings",
    )
    for table in user_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""CREATE POLICY {table}_user_scope ON {table}
                USING (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)
                WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::uuid)"""
        )
    op.execute("ALTER TABLE profiles ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE profiles FORCE ROW LEVEL SECURITY")
    op.execute(
        """CREATE POLICY profiles_user_scope ON profiles
            USING (id = NULLIF(current_setting('app.user_id', true), '')::uuid)
            WITH CHECK (id = NULLIF(current_setting('app.user_id', true), '')::uuid)"""
    )
    op.execute(
        """ALTER TABLE scenario_versions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE scenario_versions FORCE ROW LEVEL SECURITY;
        CREATE POLICY scenario_versions_user_scope ON scenario_versions
            USING (EXISTS (
                SELECT 1 FROM scenarios s WHERE s.id = scenario_id
                AND s.user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            ))
            WITH CHECK (EXISTS (
                SELECT 1 FROM scenarios s WHERE s.id = scenario_id
                AND s.user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            ));
        ALTER TABLE scenario_branches ENABLE ROW LEVEL SECURITY;
        ALTER TABLE scenario_branches FORCE ROW LEVEL SECURITY;
        CREATE POLICY scenario_branches_user_scope ON scenario_branches
            USING (EXISTS (
                SELECT 1 FROM scenarios s WHERE s.id = scenario_id
                AND s.user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            ))
            WITH CHECK (EXISTS (
                SELECT 1 FROM scenarios s WHERE s.id = scenario_id
                AND s.user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            ));
        ALTER TABLE research_sources ENABLE ROW LEVEL SECURITY;
        ALTER TABLE research_sources FORCE ROW LEVEL SECURITY;
        CREATE POLICY research_sources_user_scope ON research_sources
            USING (EXISTS (
                SELECT 1 FROM research_queries q WHERE q.id = research_query_id
                AND q.user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            ))
            WITH CHECK (EXISTS (
                SELECT 1 FROM research_queries q WHERE q.id = research_query_id
                AND q.user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            ));"""
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS embeddings;
        DROP TABLE IF EXISTS document_chunks;
        DROP TABLE IF EXISTS documents;
        DROP TABLE IF EXISTS files;
        DROP TABLE IF EXISTS memories;
        DROP TABLE IF EXISTS runs;
        DROP TABLE IF EXISTS assumptions;
        DROP TABLE IF EXISTS evidence;
        DROP TABLE IF EXISTS research_sources;
        DROP TABLE IF EXISTS research_queries;
        DROP TABLE IF EXISTS scenario_branches;
        DROP TABLE IF EXISTS scenario_versions;
        DROP TABLE IF EXISTS scenarios;
        DROP TABLE IF EXISTS commitments;
        DROP TABLE IF EXISTS constraints;
        DROP TABLE IF EXISTS goals;
        DROP TABLE IF EXISTS profiles;
        """
    )