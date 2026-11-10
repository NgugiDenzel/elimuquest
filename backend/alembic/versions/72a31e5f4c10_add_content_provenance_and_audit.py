"""add content provenance and status audit events

Revision ID: 72a31e5f4c10
Revises: a4c73e6b91d2
Create Date: 2026-10-30 01:24:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "72a31e5f4c10"
down_revision: str | None = "a4c73e6b91d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("lessons") as batch_op:
        batch_op.add_column(
            sa.Column(
                "source_category",
                sa.String(length=32),
                nullable=False,
                server_default="awaiting_verification",
            ),
        )
        batch_op.add_column(
            sa.Column(
                "rights_status",
                sa.String(length=32),
                nullable=False,
                server_default="unverified",
            ),
        )
        batch_op.create_check_constraint(
            "ck_lesson_source_category",
            "source_category IN ('awaiting_verification', 'official_curriculum', "
            "'licensed_educational', 'public_domain', 'open_educational_resource', "
            "'original_elimuquest')",
        )
        batch_op.create_check_constraint(
            "ck_lesson_source_rights_status",
            "(source_category = 'awaiting_verification' AND rights_status = 'unverified') OR "
            "(source_category = 'original_elimuquest' AND "
            "rights_status = 'not_applicable_original') OR "
            "(source_category IN ('official_curriculum', 'licensed_educational', "
            "'public_domain', 'open_educational_resource') AND "
            "rights_status IN ('unverified', 'cleared', 'restricted'))",
        )
    op.create_table(
        "content_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lesson_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("previous_status", sa.String(length=20), nullable=False),
        sa.Column("next_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_content_audit_events_actor_id"),
        "content_audit_events",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_audit_events_lesson_id"),
        "content_audit_events",
        ["lesson_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_content_audit_events_lesson_id"), table_name="content_audit_events")
    op.drop_index(op.f("ix_content_audit_events_actor_id"), table_name="content_audit_events")
    op.drop_table("content_audit_events")
    with op.batch_alter_table("lessons") as batch_op:
        batch_op.drop_constraint("ck_lesson_source_rights_status", type_="check")
        batch_op.drop_constraint("ck_lesson_source_category", type_="check")
        batch_op.drop_column("rights_status")
        batch_op.drop_column("source_category")
