"""Phase 5 concise agent execution metadata.

Revision ID: 20261004_0003
Revises: 20261003_0002
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20261004_0003"
down_revision: Union[str, None] = "20261003_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE agent_runs (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
            run_id uuid NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
            parent_run_id uuid,
            agent_name text NOT NULL,
            agent_version text NOT NULL,
            model_identifier text NOT NULL,
            prompt_version text NOT NULL,
            status text NOT NULL,
            started_at timestamptz NOT NULL,
            completed_at timestamptz,
            input_hash text NOT NULL,
            output_hash text,
            error_category text,
            error_message text,
            tool_calls jsonb NOT NULL DEFAULT '[]'::jsonb,
            output_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb
        );
        CREATE INDEX ix_agent_runs_user_id ON agent_runs(user_id);
        CREATE INDEX ix_agent_runs_run_id ON agent_runs(run_id);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE agent_runs")
