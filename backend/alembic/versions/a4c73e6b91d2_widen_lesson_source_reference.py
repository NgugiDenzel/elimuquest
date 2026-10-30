"""widen lesson source references without truncation

Revision ID: a4c73e6b91d2
Revises: 6f819c73f5d4
Create Date: 2026-10-30 16:22:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a4c73e6b91d2"
down_revision: str | None = "6f819c73f5d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("lessons") as batch_op:
        batch_op.alter_column(
            "source_reference",
            existing_type=sa.String(length=240),
            type_=sa.Text(),
            existing_nullable=True,
        )


def downgrade() -> None:
    connection = op.get_bind()
    lessons = sa.table("lessons", sa.column("source_reference", sa.Text()))
    overlength_count = connection.scalar(
        sa.select(sa.func.count()).select_from(lessons).where(
            sa.func.length(lessons.c.source_reference) > 240
        )
    )
    if overlength_count:
        raise RuntimeError(
            "Cannot narrow lessons.source_reference: values longer than 240 characters exist"
        )
    with op.batch_alter_table("lessons") as batch_op:
        batch_op.alter_column(
            "source_reference",
            existing_type=sa.Text(),
            type_=sa.String(length=240),
            existing_nullable=True,
        )
