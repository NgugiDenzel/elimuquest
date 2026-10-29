"""track AI-assisted curriculum drafts

Revision ID: 6f819c73f5d4
Revises: 9610475c2ba8
Create Date: 2026-10-24 00:37:50.743350
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "6f819c73f5d4"
down_revision: str | None = "9610475c2ba8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "lessons",
        sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("lessons", "ai_generated")
