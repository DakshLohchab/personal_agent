"""Add Phase 7 memory confirmation metadata.

Revision ID: 20261006_0004
Revises: 20261004_0003
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20261006_0004"
down_revision: Union[str, None] = "20261004_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE memories ADD COLUMN last_confirmed_at timestamptz")


def downgrade() -> None:
    op.execute("ALTER TABLE memories DROP COLUMN last_confirmed_at")
