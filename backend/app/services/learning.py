from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.curriculum.catalog import level_for
from app.models import (
    Achievement,
    DailyActivity,
    Lesson,
    LessonProgress,
    Subject,
    Topic,
    User,
    UserAchievement,
    XpTransaction,
)
from app.schemas.api import LessonResponse, QuestionResponse, SubjectResponse


def local_today(user: User) -> date:
    return datetime.now(ZoneInfo(user.timezone or "Africa/Nairobi")).date()


def total_xp(db: Session, user_id) -> int:
    return (
        db.scalar(
            select(func.coalesce(func.sum(XpTransaction.amount), 0)).where(
                XpTransaction.user_id == user_id
            )
        )
        or 0
    )


def activity_streak(db: Session, user: User) -> int:
    dates = db.scalars(
        select(DailyActivity.local_date)
        .where(DailyActivity.user_id == user.id, DailyActivity.xp_earned > 0)
        .order_by(DailyActivity.local_date.desc())
    ).all()
    if not dates:
        return 0
    today = local_today(user)
    expected = today if dates[0] == today else today - timedelta(days=1)
    if dates[0] != expected:
        return 0
    streak = 0
    for activity_date in dates:
        if activity_date != expected:
            break
        streak += 1
        expected -= timedelta(days=1)
    return streak


def lesson_schema(lesson: Lesson) -> LessonResponse:
    topic = lesson.topic
    subject = topic.subject
    selection = level_for(subject.curriculum_system, subject.curriculum_level)
    return LessonResponse(
        id=lesson.slug,
        title=lesson.title,
        description=lesson.description,
        content=lesson.content,
        topic=topic.name,
        subject=subject.name,
        curriculum_system=subject.curriculum_system,
        curriculum_level=subject.curriculum_level,
        curriculum_version=subject.curriculum_version,
        curriculum_label=selection.label if selection else subject.curriculum_level,
        learning_objectives=lesson.learning_objectives,
        prerequisites=lesson.prerequisites,
        explanation_sections=lesson.explanation_sections,
        worked_examples=lesson.worked_examples,
        source_id=lesson.source_id,
        source_reference=lesson.source_reference,
        questions=[
            QuestionResponse(
                id=q.id,
                prompt=q.prompt,
                question_type=q.question_type,
                options=q.options,
            )
            for q in lesson.questions
        ],
    )


def subject_schema(db: Session, user: User, subject: Subject) -> SubjectResponse:
    selection = level_for(subject.curriculum_system, subject.curriculum_level)
    lesson_rows = db.execute(
        select(Lesson, LessonProgress)
        .join(Topic, Topic.id == Lesson.topic_id)
        .outerjoin(
            LessonProgress,
            (LessonProgress.lesson_id == Lesson.id) & (LessonProgress.user_id == user.id),
        )
        .where(
            Topic.subject_id == subject.id,
            Lesson.published.is_(True),
            Lesson.content_status == "published",
        )
        .order_by(Lesson.sort_order, Lesson.title)
    ).all()
    published = [(lesson, progress) for lesson, progress in lesson_rows]
    completed = sum(progress is not None for _, progress in published)
    next_lesson = next(
        (lesson.title for lesson, progress in published if progress is None),
        published[0][0].title if published else None,
    )
    return SubjectResponse(
        id=subject.slug,
        name=subject.name,
        code=subject.code,
        description=subject.description,
        accent=subject.accent,
        icon=subject.icon,
        curriculum_system=subject.curriculum_system,
        curriculum_level=subject.curriculum_level,
        curriculum_version=subject.curriculum_version,
        curriculum_label=selection.label if selection else subject.curriculum_level,
        discipline_group=subject.discipline_group,
        source_id=subject.source_id,
        progress=round(completed * 100 / len(published)) if published else 0,
        lessons=len(published),
        ready=bool(published),
        next_lesson=next_lesson,
    )


def award_eligible_achievements(db: Session, user: User, new_total_xp: int) -> None:
    completed = (
        db.scalar(select(func.count(LessonProgress.id)).where(LessonProgress.user_id == user.id))
        or 0
    )
    achievements = db.scalars(select(Achievement)).all()
    existing = set(
        db.scalars(
            select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)
        ).all()
    )
    for achievement in achievements:
        if achievement.id in existing:
            continue
        if new_total_xp >= achievement.xp_threshold and completed >= achievement.lesson_threshold:
            db.add(UserAchievement(user_id=user.id, achievement_id=achievement.id))
