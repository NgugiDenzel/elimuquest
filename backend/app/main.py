import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.dependencies import admin_user
from app.api.v1.router import router as v1_router
from app.content.schema import validate_source_locator
from app.core.config import settings
from app.curriculum.catalog import SOURCE_IDS
from app.db.session import get_db
from app.models import Lesson, Subject, Topic, User

logging.basicConfig(level=settings.log_level.upper())


def curriculum_alignment_status(lesson: Lesson) -> str:
    if lesson.source_reference:
        try:
            validate_source_locator(lesson.source_reference)
        except ValueError:
            return "partially_verified"
    if lesson.source_id and lesson.source_id in SOURCE_IDS:
        return "officially_verified" if lesson.source_reference else "partially_verified"
    return "unverified"


def quality_status(lesson: Lesson) -> str:
    if not lesson.explanation_sections or not lesson.questions:
        return "needs_review"
    if any(
        not question.correct_answer.strip()
        or (
            question.question_type == "multiple_choice"
            and (
                not question.explanation
                or question.correct_answer not in (question.options or [])
            )
        )
        or (question.question_type == "short_answer" and bool(question.options))
        for question in lesson.questions
    ):
        return "needs_review"
    return "validated"


app = FastAPI(title="ElimuQuest API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/readiness")
def readiness(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.get("/api/v1/admin/lessons")
def admin_lessons(
    _: User = Depends(admin_user),
    db: Session = Depends(get_db),
):
    lessons = db.scalars(
        select(Lesson)
        .options(
            joinedload(Lesson.topic).joinedload(Topic.subject),
            selectinload(Lesson.questions),
        )
        .join(Topic)
        .join(Subject)
        .order_by(Subject.name, Topic.name, Lesson.sort_order, Lesson.title)
    ).all()
    return {
        "items": [
            {
                "id": lesson.slug,
                "title": lesson.title,
                "topic": lesson.topic.name,
                "subject": lesson.topic.subject.name,
                "curriculum_system": lesson.topic.subject.curriculum_system,
                "curriculum_level": lesson.topic.subject.curriculum_level,
                "curriculum_version": lesson.topic.subject.curriculum_version,
                "content_version": lesson.content_version,
                "description": lesson.description,
                "content": lesson.content,
                "learning_objectives": lesson.learning_objectives,
                "explanation_sections": lesson.explanation_sections,
                "worked_examples": lesson.worked_examples,
                "questions": [
                    {
                        "prompt": question.prompt,
                        "question_type": question.question_type,
                        "options": question.options,
                        "correct_answer": question.correct_answer,
                        "explanation": question.explanation,
                        "difficulty": question.difficulty,
                    }
                    for question in lesson.questions
                ],
                "published": lesson.published,
                "status": lesson.content_status,
                "ai_generated": lesson.ai_generated,
                "is_demo": lesson.is_demo,
                "source_id": lesson.source_id,
                "source_reference": lesson.source_reference,
                "author": lesson.author,
                "reviewer": lesson.reviewer,
                "curriculum_alignment": curriculum_alignment_status(lesson),
                "quality_status": quality_status(lesson),
            }
            for lesson in lessons
        ],
        "count": len(lessons),
    }
