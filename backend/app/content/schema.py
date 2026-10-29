import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.curriculum.catalog import SOURCE_IDS, level_for, subject_for_slug


class ExplanationSection(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1)


class WorkedExample(BaseModel):
    prompt: str = Field(min_length=1)
    solution: str = Field(min_length=1)
    reasoning: str = Field(min_length=1)


class QuestionPackage(BaseModel):
    prompt: str = Field(min_length=1)
    question_type: Literal["multiple_choice", "short_answer"] = "multiple_choice"
    options: list[str] = Field(default_factory=list, max_length=8)
    correct_answer: str = Field(min_length=1, max_length=500)
    explanation: str = ""
    difficulty: Literal["foundational", "intermediate", "advanced"] = "foundational"

    @field_validator("options")
    @classmethod
    def validate_options(cls, options: list[str]) -> list[str]:
        if len(options) > 8:
            raise ValueError("Answer options must contain at most 8 entries")
        normalized = [option.strip().casefold() for option in options]
        if any(not option for option in normalized) or len(set(normalized)) != len(normalized):
            raise ValueError("Answer options must be non-empty and unique")
        return [option.strip() for option in options]

    @model_validator(mode="after")
    def validate_answer_key(self) -> "QuestionPackage":
        if self.question_type == "multiple_choice":
            if not 2 <= len(self.options) <= 8:
                raise ValueError("Multiple-choice questions need between 2 and 8 options")
            if self.correct_answer.strip().casefold() not in {
                option.strip().casefold() for option in self.options
            }:
                raise ValueError("Correct answer must match one of the options")
            if not self.explanation.strip():
                raise ValueError("Multiple-choice questions need an answer explanation")
        elif self.options:
            raise ValueError("Short-answer questions must not include answer options")
        return self


class LessonPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)
    content_version: int = Field(default=1, ge=1)
    sort_order: int = Field(default=0, ge=0)
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=1)
    content: str = ""
    learning_objectives: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    explanation_sections: list[ExplanationSection] = Field(default_factory=list)
    worked_examples: list[WorkedExample] = Field(default_factory=list)
    source_reference: str | None = None
    author: str = Field(min_length=3, max_length=320)
    questions: list[QuestionPackage] = Field(min_length=1)

    @field_validator("source_reference")
    @classmethod
    def validate_source_reference(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        return validate_source_locator(value)

    @field_validator("learning_objectives", "prerequisites")
    @classmethod
    def validate_text_lists(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("Text-list entries must not be blank")
        return [value.strip() for value in values]

    @model_validator(mode="after")
    def detect_duplicate_questions(self) -> "LessonPackage":
        prompts = [
            re.sub(r"\s+", " ", question.prompt).strip().casefold() for question in self.questions
        ]
        if len(prompts) != len(set(prompts)):
            raise ValueError("Duplicate question prompts are not allowed")
        return self


class ContentPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    ai_generated: bool = False
    is_demo: bool = False
    curriculum_system: str
    curriculum_level: str
    curriculum_version: str
    subject_slug: str
    topic_slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=80)
    topic_name: str = Field(min_length=1, max_length=160)
    topic_source_reference: str | None = None
    source_id: str | None = None
    lessons: list[LessonPackage] = Field(min_length=1)

    @field_validator("topic_source_reference")
    @classmethod
    def validate_topic_reference(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        return validate_source_locator(value)

    @model_validator(mode="after")
    def validate_curriculum_mapping(self) -> "ContentPackage":
        selection = level_for(self.curriculum_system, self.curriculum_level)
        if selection is None:
            raise ValueError("Unsupported curriculum system and level")
        if self.curriculum_version != selection.version:
            raise ValueError("Curriculum version does not match the registered selection")
        subject = subject_for_slug(self.subject_slug)
        if subject is None or subject[0] != selection:
            raise ValueError("Subject is not available in the selected curriculum and level")
        if (
            self.source_id is not None
            and self.source_id not in SOURCE_IDS
            and self.source_id != selection.source_id
        ):
            # Content can still be published when its curriculum alignment is unverified or
            # independently sourced. Official KICD metadata remains optional, not required.
            pass
        slugs = [lesson.slug for lesson in self.lessons]
        if len(slugs) != len(set(slugs)):
            raise ValueError("Lesson slugs must be unique within the package")
        return self


def validate_source_locator(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if re.search(r"\b(fixture|placeholder|tbd|replace|example only)\b", value, re.IGNORECASE):
        raise ValueError("Replace placeholder provenance with a verified curriculum citation")
    locator = re.search(
        r"(?:\bpages?\s+\d+(?:[-–]\d+)?|\bpp?\.\s*\d+(?:[-–]\d+)?|\bsection\s+[\w.-]+|\bstrand\s+[\w.-]+|\bsub-strand\s+[\w.-]+)",
        value,
        re.IGNORECASE,
    )
    if not locator:
        raise ValueError("Cite a page, section, strand or sub-strand from the source")
    return value
