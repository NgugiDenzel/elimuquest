"""add Number Systems educator review and learner feedback

Revision ID: 2c8a47f1d963
Revises: 72a31e5f4c10
Create Date: 2026-11-09 16:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "2c8a47f1d963"
down_revision: str | None = "72a31e5f4c10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mathematics_review_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("item_id", sa.String(length=240), nullable=False),
        sa.Column("decision", sa.String(length=24), nullable=False),
        sa.Column("comments", sa.Text(), nullable=False),
        sa.Column("correction", sa.Text(), nullable=False),
        sa.Column("mathematical_error_flag", sa.Boolean(), nullable=False),
        sa.Column("previous_state", sa.String(length=24), nullable=False),
        sa.Column("new_state", sa.String(length=24), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "item_type IN ('topic', 'alignment', 'lesson', 'outcome', 'question')",
            name="ck_math_review_item_type",
        ),
        sa.CheckConstraint(
            "decision IN ('pending_review', 'approved', 'revision_requested', 'rejected')",
            name="ck_math_review_decision",
        ),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_math_review_item_created",
        "mathematics_review_decisions",
        ["item_type", "item_id", "created_at"],
    )
    op.create_index(
        op.f("ix_mathematics_review_decisions_item_id"),
        "mathematics_review_decisions",
        ["item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mathematics_review_decisions_reviewer_id"),
        "mathematics_review_decisions",
        ["reviewer_id"],
        unique=False,
    )
    op.create_table(
        "learner_content_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("lesson_id", sa.String(length=120), nullable=False),
        sa.Column("question_id", sa.String(length=120), nullable=True),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "category IN ('incorrect_explanation', 'confusing_question', "
            "'broken_diagram', 'navigation_issue', 'technical_error', 'general')",
            name="ck_learner_feedback_category",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_learner_content_feedback_user_id"),
        "learner_content_feedback",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_learner_content_feedback_user_id"),
        table_name="learner_content_feedback",
    )
    op.drop_table("learner_content_feedback")
    op.drop_index(
        op.f("ix_mathematics_review_decisions_reviewer_id"),
        table_name="mathematics_review_decisions",
    )
    op.drop_index(
        op.f("ix_mathematics_review_decisions_item_id"),
        table_name="mathematics_review_decisions",
    )
    op.drop_index("ix_math_review_item_created", table_name="mathematics_review_decisions")
    op.drop_table("mathematics_review_decisions")
