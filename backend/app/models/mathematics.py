from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.entities import Base, User, now_utc


class MathematicsReviewDecision(Base):
    __tablename__ = "mathematics_review_decisions"
    __table_args__ = (
        CheckConstraint(
            "item_type IN ('topic', 'alignment', 'lesson', 'outcome', 'question')",
            name="ck_math_review_item_type",
        ),
        CheckConstraint(
            "decision IN ('pending_review', 'approved', 'revision_requested', 'rejected')",
            name="ck_math_review_decision",
        ),
        Index("ix_math_review_item_created", "item_type", "item_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    item_type: Mapped[str] = mapped_column(String(20))
    item_id: Mapped[str] = mapped_column(String(240), index=True)
    decision: Mapped[str] = mapped_column(String(24))
    comments: Mapped[str] = mapped_column(Text, default="")
    correction: Mapped[str] = mapped_column(Text, default="")
    mathematical_error_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    previous_state: Mapped[str] = mapped_column(String(24))
    new_state: Mapped[str] = mapped_column(String(24))
    reviewer_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    reviewer: Mapped[User] = relationship()


class LearnerContentFeedback(Base):
    __tablename__ = "learner_content_feedback"
    __table_args__ = (
        CheckConstraint(
            "category IN ('incorrect_explanation', 'confusing_question', "
            "'broken_diagram', 'navigation_issue', 'technical_error', 'general')",
            name="ck_learner_feedback_category",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    lesson_id: Mapped[str] = mapped_column(String(120))
    question_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    user: Mapped[User | None] = relationship()
