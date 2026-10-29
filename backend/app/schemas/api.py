from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.curriculum.catalog import level_for


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class RegisterRequest(Credentials):
    full_name: str = Field(min_length=2, max_length=120)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    form: str
    curriculum_system: str
    curriculum_level: str
    timezone: str
    daily_goal_xp: int

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    form: str | None = Field(default=None, max_length=20)
    curriculum_system: str | None = Field(default=None, max_length=20)
    curriculum_level: str | None = Field(default=None, max_length=20)
    timezone: str | None = Field(default=None, max_length=64)
    daily_goal_xp: int | None = Field(default=None, ge=10, le=200)

    @model_validator(mode="after")
    def validate_curriculum_selection(self) -> "ProfileUpdate":
        if (self.curriculum_system is None) != (self.curriculum_level is None):
            raise ValueError("Select both curriculum_system and curriculum_level together")
        if (
            self.curriculum_system is not None
            and level_for(self.curriculum_system, self.curriculum_level or "") is None
        ):
            raise ValueError("Unsupported curriculum and level selection")
        return self

    @model_validator(mode="after")
    def align_legacy_form(self) -> "ProfileUpdate":
        if self.curriculum_level is not None:
            self.form = self.curriculum_level
        elif self.form is not None and self.curriculum_system is not None:
            raise ValueError("Use curriculum_level when changing curriculum selection")
        return self

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is not None:
            from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

            try:
                ZoneInfo(value)
            except ZoneInfoNotFoundError as exc:
                raise ValueError("Use a valid IANA timezone") from exc
        return value


class SubjectResponse(BaseModel):
    id: str
    name: str
    code: str
    description: str
    accent: str
    icon: str
    curriculum_system: str
    curriculum_level: str
    curriculum_version: str
    curriculum_label: str
    discipline_group: str | None
    source_id: str | None
    progress: int
    lessons: int
    ready: bool
    next_lesson: str | None


class QuestionResponse(BaseModel):
    id: UUID
    prompt: str
    question_type: Literal["multiple_choice", "short_answer"]
    options: list[str]


class LessonResponse(BaseModel):
    id: str
    title: str
    description: str
    content: str
    topic: str
    subject: str
    curriculum_system: str
    curriculum_level: str
    curriculum_version: str
    curriculum_label: str
    learning_objectives: list[str]
    prerequisites: list[str]
    explanation_sections: list[dict[str, str]]
    worked_examples: list[dict[str, str]]
    source_id: str | None
    source_reference: str | None
    questions: list[QuestionResponse]


class ContentStatusUpdate(BaseModel):
    status: str = Field(pattern="^(draft|in_review|approved|published|archived)$")


class StartSessionRequest(BaseModel):
    lesson_id: str = Field(min_length=1, max_length=100)


class SessionResponse(BaseModel):
    id: UUID
    lesson: LessonResponse
    completed_at: datetime | None = None


class AnswerRequest(BaseModel):
    question_id: UUID
    answer: str = Field(min_length=1, max_length=500)


class AnswerResponse(BaseModel):
    question_id: UUID
    correct: bool
    explanation: str


class CompletionResponse(BaseModel):
    session_id: UUID
    score_percent: int
    correct_answers: int
    total_questions: int
    xp_awarded: int
    total_xp: int
    streak_days: int
    daily_goal_xp: int
    daily_progress_xp: int
    already_completed: bool


class DashboardResponse(BaseModel):
    student: ProfileResponse
    total_xp: int
    league_rank: int | None
    streak_days: int
    daily_goal_xp: int
    daily_progress_xp: int
    lessons_completed: int
    accuracy: int
    subjects: list[SubjectResponse]
    current_lesson: LessonResponse | None


class ActivityDay(BaseModel):
    label: str
    xp: int


class SubjectProgress(BaseModel):
    subject: str
    progress: int
    accent: str


class ProgressResponse(BaseModel):
    total_xp: int
    lessons_completed: int
    lessons_attempted: int
    accuracy: int
    weekly_activity: list[ActivityDay]
    mastery: list[SubjectProgress]
    strongest_topics: list[str]
    needs_review: list[str]


class LeaderboardEntry(BaseModel):
    rank: int
    name: str
    xp: int
    streak: int
