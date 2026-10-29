"""add curriculum metadata and review states

Revision ID: 9610475c2ba8
Revises: b60788453753
Create Date: 2026-10-24 00:21:38.109251
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9610475c2ba8"
down_revision: str | None = "b60788453753"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "lesson_questions",
        sa.Column(
            "question_type", sa.String(length=20), nullable=False, server_default="multiple_choice"
        ),
    )
    op.add_column(
        "lesson_questions",
        sa.Column(
            "difficulty", sa.String(length=20), nullable=False, server_default="foundational"
        ),
    )
    op.add_column(
        "lessons",
        sa.Column("learning_objectives", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column(
        "lessons",
        sa.Column("prerequisites", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column(
        "lessons",
        sa.Column(
            "explanation_sections", sa.JSON(), nullable=False, server_default=sa.text("'[]'")
        ),
    )
    op.add_column(
        "lessons",
        sa.Column("worked_examples", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column(
        "lessons",
        sa.Column("content_status", sa.String(length=20), nullable=False, server_default="draft"),
    )
    op.add_column(
        "lessons",
        sa.Column("content_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column("lessons", sa.Column("source_id", sa.String(length=80), nullable=True))
    op.add_column("lessons", sa.Column("source_reference", sa.String(length=240), nullable=True))
    op.add_column("lessons", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column("lessons", sa.Column("author", sa.String(length=320), nullable=True))
    op.add_column("lessons", sa.Column("reviewer", sa.String(length=320), nullable=True))
    op.add_column("lessons", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("lessons", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "subjects",
        sa.Column(
            "curriculum_system", sa.String(length=20), nullable=False, server_default="LEGACY"
        ),
    )
    op.add_column(
        "subjects",
        sa.Column(
            "curriculum_level", sa.String(length=20), nullable=False, server_default="Legacy"
        ),
    )
    op.add_column(
        "subjects",
        sa.Column(
            "curriculum_version", sa.String(length=64), nullable=False, server_default="legacy-demo"
        ),
    )
    op.add_column("subjects", sa.Column("source_id", sa.String(length=80), nullable=True))
    op.add_column("subjects", sa.Column("discipline_group", sa.String(length=40), nullable=True))
    op.add_column("topics", sa.Column("source_reference", sa.String(length=240), nullable=True))
    op.add_column("topics", sa.Column("discipline_group", sa.String(length=40), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "curriculum_system", sa.String(length=20), nullable=False, server_default="LEGACY"
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "curriculum_level", sa.String(length=20), nullable=False, server_default="Legacy"
        ),
    )
    op.execute(
        "UPDATE lessons SET content_status = CASE WHEN published THEN 'published' ELSE 'draft' END"
    )
    with op.batch_alter_table("lessons") as batch:
        batch.create_check_constraint(
            "ck_lesson_content_status",
            "content_status IN ('draft', 'in_review', 'approved', 'published', 'archived')",
        )


def downgrade() -> None:
    with op.batch_alter_table("lessons") as batch:
        batch.drop_constraint("ck_lesson_content_status", type_="check")
    for table, column in (
        ("users", "curriculum_level"),
        ("users", "curriculum_system"),
        ("topics", "discipline_group"),
        ("topics", "source_reference"),
        ("subjects", "discipline_group"),
        ("subjects", "source_id"),
        ("subjects", "curriculum_version"),
        ("subjects", "curriculum_level"),
        ("subjects", "curriculum_system"),
        ("lessons", "published_at"),
        ("lessons", "reviewed_at"),
        ("lessons", "reviewer"),
        ("lessons", "author"),
        ("lessons", "source_reference"),
        ("lessons", "content_hash"),
        ("lessons", "source_id"),
        ("lessons", "content_version"),
        ("lessons", "content_status"),
        ("lessons", "worked_examples"),
        ("lessons", "explanation_sections"),
        ("lessons", "prerequisites"),
        ("lessons", "learning_objectives"),
        ("lesson_questions", "difficulty"),
        ("lesson_questions", "question_type"),
    ):
        op.drop_column(table, column)
