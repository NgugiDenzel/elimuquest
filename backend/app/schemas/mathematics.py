from typing import Literal

from pydantic import BaseModel, Field


class MathematicsReviewDecisionRequest(BaseModel):
    item_type: Literal["topic", "alignment", "lesson", "outcome", "question"]
    item_id: str = Field(min_length=1, max_length=240)
    decision: Literal["pending_review", "approved", "revision_requested", "rejected"]
    comments: str = Field(default="", max_length=4000)
    correction: str = Field(default="", max_length=4000)
    mathematical_error_flag: bool = False


class LearnerContentFeedbackRequest(BaseModel):
    lesson_id: str = Field(min_length=1, max_length=120)
    question_id: str | None = Field(default=None, max_length=120)
    category: Literal[
        "incorrect_explanation",
        "confusing_question",
        "broken_diagram",
        "navigation_issue",
        "technical_error",
        "general",
    ]
    message: str = Field(min_length=3, max_length=2000)


class MathematicsAnswerRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=100)
    answer: str = Field(min_length=1, max_length=500)


class MathematicsAnswerFeedback(BaseModel):
    question_id: str
    submitted: bool = True
    correct: bool
    correct_answer: str
    explanation: str
    review_topic: str
    topic_id: str | None = None
