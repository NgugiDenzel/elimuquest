import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.dependencies import admin_user, current_user
from app.content.schema import validate_source_locator
from app.core.security import create_access_token, hash_password, verify_password
from app.curriculum.catalog import SOURCE_IDS, curriculum_options, level_for
from app.db.session import get_db
from app.models import (
    AnswerAttempt,
    DailyActivity,
    Lesson,
    LessonProgress,
    LessonQuestion,
    LessonSession,
    Subject,
    Topic,
    User,
    XpTransaction,
)
from app.schemas.api import (
    AnswerRequest,
    AnswerResponse,
    CompletionResponse,
    ContentStatusUpdate,
    Credentials,
    DashboardResponse,
    LeaderboardEntry,
    ProfileResponse,
    ProfileUpdate,
    ProgressResponse,
    RegisterRequest,
    SessionResponse,
    StartSessionRequest,
    SubjectResponse,
)
from app.services.learning import (
    activity_streak,
    award_eligible_achievements,
    lesson_schema,
    local_today,
    subject_schema,
    total_xp,
)

router = APIRouter()


def _normalize_short_answer(answer: str) -> str:
    normalized = answer.strip().replace("−", "-")
    candidate = normalized.removesuffix(".")
    numeric_pattern = r"[+-]?(?:(?:\d{1,3}(?:[,\s]\d{3})+|\d+)(?:\.\d+)?|\.\d+)"
    if re.fullmatch(numeric_pattern, candidate):
        number = Decimal(candidate.replace(",", "").replace(" ", "")).normalize()
        return f"number:{number}"
    if re.fullmatch(r"[+-]?[\d,.\s]+", candidate):
        return f"invalid-number:{candidate}"
    normalized = normalized.casefold()
    normalized = re.sub(r"[,.!?;:]", "", normalized)
    normalized = re.sub(r"[-–—]", " ", normalized)
    return " ".join(normalized.split()).removesuffix(".")


def _answer_matches(question: LessonQuestion, answer: str) -> bool:
    if question.question_type == "short_answer":
        return _normalize_short_answer(answer) == _normalize_short_answer(question.correct_answer)
    return answer.strip().casefold() == question.correct_answer.strip().casefold()


def _has_supported_selection(user: User) -> bool:
    return level_for(user.curriculum_system, user.curriculum_level) is not None


def _curriculum_alignment_status(lesson: Lesson) -> str:
    if lesson.source_reference:
        try:
            validate_source_locator(lesson.source_reference)
        except ValueError:
            return "partially_verified"
    if lesson.source_id and lesson.source_id in SOURCE_IDS:
        return "officially_verified" if lesson.source_reference else "partially_verified"
    return "unverified"


def _quality_status(lesson: Lesson) -> str:
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


def _lesson_or_404(db: Session, slug: str, user: User) -> Lesson:
    if not _has_supported_selection(user):
        raise HTTPException(status_code=404, detail="Select a supported curriculum and level first")
    lesson = db.scalar(
        select(Lesson)
        .options(joinedload(Lesson.topic).joinedload(Topic.subject), selectinload(Lesson.questions))
        .join(Topic)
        .join(Subject)
        .where(
            Lesson.slug == slug,
            Lesson.published.is_(True),
            Lesson.content_status == "published",
            Subject.curriculum_system == user.curriculum_system,
            Subject.curriculum_level == user.curriculum_level,
        )
    )
    if lesson is None:
        raise HTTPException(status_code=404, detail="Published lesson not found")
    return lesson


def _session_or_404(db: Session, user: User, session_id: UUID) -> LessonSession:
    session = db.scalar(
        select(LessonSession)
        .options(
            selectinload(LessonSession.lesson).selectinload(Lesson.questions),
            selectinload(LessonSession.lesson).joinedload(Lesson.topic).joinedload(Topic.subject),
            selectinload(LessonSession.attempts),
        )
        .join(LessonSession.lesson)
        .join(Lesson.topic)
        .join(Topic.subject)
        .where(
            LessonSession.id == session_id,
            LessonSession.user_id == user.id,
            Subject.curriculum_system == user.curriculum_system,
            Subject.curriculum_level == user.curriculum_level,
        )
        .with_for_update()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Lesson session not found")
    return session


@router.post("/auth/register", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=dict[str, str])
def login(payload: Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=401,
            detail="Email or password is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}


@router.get("/me", response_model=ProfileResponse)
def me(user: User = Depends(current_user)):
    return user


@router.patch("/me/profile", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(user, key, value)
    if payload.curriculum_level is not None:
        user.form = payload.curriculum_level
    db.commit()
    db.refresh(user)
    return user


@router.get("/curricula")
def curricula(_: User = Depends(current_user)):
    return {"items": curriculum_options()}


@router.get("/subjects", response_model=list[SubjectResponse])
def subjects(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not _has_supported_selection(user):
        return []
    rows = db.scalars(
        select(Subject)
        .where(
            Subject.curriculum_system == user.curriculum_system,
            Subject.curriculum_level == user.curriculum_level,
        )
        .order_by(Subject.name)
    ).all()
    return [subject_schema(db, user, subject) for subject in rows]


@router.get("/subjects/{subject_id}", response_model=SubjectResponse)
def subject_detail(
    subject_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    if not _has_supported_selection(user):
        raise HTTPException(status_code=404, detail="Select a supported curriculum and level first")
    subject = db.scalar(
        select(Subject).where(
            Subject.slug == subject_id,
            Subject.curriculum_system == user.curriculum_system,
            Subject.curriculum_level == user.curriculum_level,
        )
    )
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject_schema(db, user, subject)


@router.get("/subjects/{subject_id}/learning-path")
def learning_path(
    subject_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    if not _has_supported_selection(user):
        raise HTTPException(status_code=404, detail="Select a supported curriculum and level first")
    subject = db.scalar(
        select(Subject).where(
            Subject.slug == subject_id,
            Subject.curriculum_system == user.curriculum_system,
            Subject.curriculum_level == user.curriculum_level,
        )
    )
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    lessons = db.scalars(
        select(Lesson)
        .join(Topic)
        .options(joinedload(Lesson.topic).joinedload(Topic.subject), selectinload(Lesson.questions))
        .where(
            Topic.subject_id == subject.id,
            Lesson.published.is_(True),
            Lesson.content_status == "published",
        )
        .order_by(Lesson.sort_order, Lesson.title)
    ).all()
    completed_ids = set(
        db.scalars(
            select(LessonProgress.lesson_id).where(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id.in_([lesson.id for lesson in lessons] or [UUID(int=0)]),
            )
        ).all()
    )
    selection = level_for(subject.curriculum_system, subject.curriculum_level)
    return {
        "subject": subject.slug,
        "curriculum_system": subject.curriculum_system,
        "curriculum_level": subject.curriculum_level,
        "curriculum_version": subject.curriculum_version,
        "curriculum_label": selection.label if selection else subject.curriculum_level,
        "lessons": [
            {
                "id": lesson.slug,
                "title": lesson.title,
                "description": lesson.description,
                "completed": lesson.id in completed_ids,
                "questions_count": len(lesson.questions),
            }
            for lesson in lessons
        ],
    }


@router.get("/lessons/{lesson_id}")
def lesson_detail(
    lesson_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    return lesson_schema(_lesson_or_404(db, lesson_id, user))


@router.post("/lesson-sessions", response_model=SessionResponse, status_code=201)
def start_session(
    payload: StartSessionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    lesson = _lesson_or_404(db, payload.lesson_id, user)
    if not lesson.questions:
        raise HTTPException(status_code=409, detail="Lesson has no available questions")
    session = LessonSession(user_id=user.id, lesson_id=lesson.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionResponse(id=session.id, lesson=lesson_schema(lesson))


@router.get("/lesson-sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    session = _session_or_404(db, user, session_id)
    return SessionResponse(
        id=session.id,
        lesson=lesson_schema(session.lesson),
        completed_at=session.completed_at,
    )


@router.post("/lesson-sessions/{session_id}/answers", response_model=AnswerResponse)
def submit_answer(
    session_id: UUID,
    payload: AnswerRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    session = _session_or_404(db, user, session_id)
    if session.completed_at:
        raise HTTPException(status_code=409, detail="This lesson session is already complete")
    question = next((q for q in session.lesson.questions if q.id == payload.question_id), None)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found in this lesson")
    if any(attempt.question_id == question.id for attempt in session.attempts):
        raise HTTPException(
            status_code=409, detail="An answer was already submitted for this question"
        )
    is_correct = _answer_matches(question, payload.answer)
    db.add(
        AnswerAttempt(
            session_id=session.id,
            question_id=question.id,
            answer=payload.answer.strip(),
            is_correct=is_correct,
        )
    )
    db.commit()
    explanation = question.explanation
    if question.question_type == "short_answer" and not is_correct:
        explanation = explanation or f"Correct answer: {question.correct_answer}"
    return AnswerResponse(
        question_id=question.id,
        correct=is_correct,
        explanation=explanation,
    )


@router.post("/lesson-sessions/{session_id}/complete", response_model=CompletionResponse)
def complete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    session = _session_or_404(db, user, session_id)
    questions_count = len(session.lesson.questions)
    if questions_count == 0:
        raise HTTPException(status_code=409, detail="Lesson has no questions")
    attempts = session.attempts
    if len(attempts) != questions_count:
        raise HTTPException(
            status_code=409, detail="Answer every question before completing the lesson"
        )
    correct_count = sum(attempt.is_correct for attempt in attempts)
    score = round(correct_count * 100 / questions_count)
    already_completed = session.completed_at is not None
    if not already_completed:
        now = datetime.now(UTC)
        xp = 10 + correct_count * 5
        session.completed_at = now
        session.score_percent = score
        session.xp_awarded = xp
        progress = db.scalar(
            select(LessonProgress).where(
                LessonProgress.user_id == user.id, LessonProgress.lesson_id == session.lesson_id
            )
        )
        if progress is None:
            db.add(
                LessonProgress(
                    user_id=user.id,
                    lesson_id=session.lesson_id,
                    attempts=1,
                    best_score_percent=score,
                    completed_at=now,
                )
            )
        else:
            progress.attempts += 1
            progress.best_score_percent = max(progress.best_score_percent, score)
            progress.completed_at = now
        db.add(
            XpTransaction(
                user_id=user.id,
                session_id=session.id,
                amount=xp,
                reason="lesson_completion",
            )
        )
        day = local_today(user)
        activity = db.scalar(
            select(DailyActivity).where(
                DailyActivity.user_id == user.id, DailyActivity.local_date == day
            )
        )
        if activity is None:
            activity = DailyActivity(
                user_id=user.id, local_date=day, xp_earned=0, lessons_completed=0
            )
            db.add(activity)
        activity.xp_earned += xp
        activity.lessons_completed += 1
        db.flush()
        award_eligible_achievements(db, user, total_xp(db, user.id))
        db.commit()
    else:
        xp = session.xp_awarded
    activity = db.scalar(
        select(DailyActivity).where(
            DailyActivity.user_id == user.id, DailyActivity.local_date == local_today(user)
        )
    )
    return CompletionResponse(
        session_id=session.id,
        score_percent=session.score_percent or score,
        correct_answers=correct_count,
        total_questions=questions_count,
        xp_awarded=xp,
        total_xp=total_xp(db, user.id),
        streak_days=activity_streak(db, user),
        daily_goal_xp=user.daily_goal_xp,
        daily_progress_xp=activity.xp_earned if activity else 0,
        already_completed=already_completed,
    )


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    has_selection = _has_supported_selection(user)
    rows = (
        db.scalars(
            select(Subject)
            .where(
                Subject.curriculum_system == user.curriculum_system,
                Subject.curriculum_level == user.curriculum_level,
            )
            .order_by(Subject.name)
        ).all()
        if has_selection
        else []
    )
    today_activity = db.scalar(
        select(DailyActivity).where(
            DailyActivity.user_id == user.id, DailyActivity.local_date == local_today(user)
        )
    )
    completed = 0
    if has_selection:
        completed = (
            db.scalar(
                select(func.count(LessonProgress.id))
                .join(Lesson, Lesson.id == LessonProgress.lesson_id)
                .join(Topic, Topic.id == Lesson.topic_id)
                .join(Subject, Subject.id == Topic.subject_id)
                .where(
                    LessonProgress.user_id == user.id,
                    Subject.curriculum_system == user.curriculum_system,
                    Subject.curriculum_level == user.curriculum_level,
                )
            )
            or 0
        )
    attempts = (
        db.scalars(
            select(AnswerAttempt)
            .join(LessonSession)
            .join(LessonSession.lesson)
            .join(Lesson.topic)
            .join(Topic.subject)
            .where(
                LessonSession.user_id == user.id,
                Subject.curriculum_system == user.curriculum_system,
                Subject.curriculum_level == user.curriculum_level,
            )
        ).all()
        if has_selection
        else []
    )
    accuracy = round(sum(a.is_correct for a in attempts) * 100 / len(attempts)) if attempts else 0
    ranking = db.execute(
        select(User.id, func.coalesce(func.sum(XpTransaction.amount), 0).label("xp"))
        .outerjoin(XpTransaction, XpTransaction.user_id == User.id)
        .where(User.is_active.is_(True), User.role == "student")
        .group_by(User.id, User.created_at)
        .order_by(func.coalesce(func.sum(XpTransaction.amount), 0).desc(), User.created_at, User.id)
    ).all()
    rank = next((index for index, row in enumerate(ranking, start=1) if row.id == user.id), None)
    next_lesson = (
        db.scalar(
            select(Lesson)
            .options(
                joinedload(Lesson.topic).joinedload(Topic.subject),
                selectinload(Lesson.questions),
            )
            .outerjoin(
                LessonProgress,
                (LessonProgress.lesson_id == Lesson.id) & (LessonProgress.user_id == user.id),
            )
            .join(Topic, Topic.id == Lesson.topic_id)
            .join(Subject, Subject.id == Topic.subject_id)
            .where(
                Lesson.published.is_(True),
                Lesson.content_status == "published",
                LessonProgress.id.is_(None),
                Subject.curriculum_system == user.curriculum_system,
                Subject.curriculum_level == user.curriculum_level,
            )
            .order_by(Lesson.sort_order)
            .limit(1)
        )
        if has_selection
        else None
    )
    return DashboardResponse(
        student=user,
        total_xp=total_xp(db, user.id),
        league_rank=rank,
        streak_days=activity_streak(db, user),
        daily_goal_xp=user.daily_goal_xp,
        daily_progress_xp=today_activity.xp_earned if today_activity else 0,
        lessons_completed=completed,
        accuracy=accuracy,
        subjects=[subject_schema(db, user, subject) for subject in rows],
        current_lesson=lesson_schema(next_lesson) if next_lesson else None,
    )


@router.get("/progress", response_model=ProgressResponse)
def progress(db: Session = Depends(get_db), user: User = Depends(current_user)):
    has_selection = _has_supported_selection(user)
    attempts = (
        db.scalars(
            select(AnswerAttempt)
            .join(LessonSession)
            .join(LessonSession.lesson)
            .join(Lesson.topic)
            .join(Topic.subject)
            .where(
                LessonSession.user_id == user.id,
                Subject.curriculum_system == user.curriculum_system,
                Subject.curriculum_level == user.curriculum_level,
            )
        ).all()
        if has_selection
        else []
    )
    completed = 0
    if has_selection:
        completed = (
            db.scalar(
                select(func.count(LessonProgress.id))
                .join(Lesson, Lesson.id == LessonProgress.lesson_id)
                .join(Topic, Topic.id == Lesson.topic_id)
                .join(Subject, Subject.id == Topic.subject_id)
                .where(
                    LessonProgress.user_id == user.id,
                    Subject.curriculum_system == user.curriculum_system,
                    Subject.curriculum_level == user.curriculum_level,
                )
            )
            or 0
        )
    activity = db.scalars(
        select(DailyActivity)
        .where(
            DailyActivity.user_id == user.id,
            DailyActivity.local_date >= local_today(user) - timedelta(days=6),
        )
        .order_by(DailyActivity.local_date)
    ).all()
    by_date = {day.local_date: day.xp_earned for day in activity}
    today = local_today(user)
    mastery = []
    subjects = (
        db.scalars(
            select(Subject)
            .where(
                Subject.curriculum_system == user.curriculum_system,
                Subject.curriculum_level == user.curriculum_level,
            )
            .order_by(Subject.name)
        ).all()
        if has_selection
        else []
    )
    for subject in subjects:
        summary = subject_schema(db, user, subject)
        mastery.append(
            {"subject": subject.name, "progress": summary.progress, "accent": subject.accent}
        )
    return ProgressResponse(
        total_xp=total_xp(db, user.id),
        lessons_completed=completed,
        lessons_attempted=(
            db.scalar(
                select(func.count(func.distinct(LessonSession.lesson_id)))
                .join(LessonSession.lesson)
                .join(Lesson.topic)
                .join(Topic.subject)
                .where(
                    LessonSession.user_id == user.id,
                    Subject.curriculum_system == user.curriculum_system,
                    Subject.curriculum_level == user.curriculum_level,
                )
            )
            or 0
        )
        if has_selection
        else 0,
        accuracy=round(sum(a.is_correct for a in attempts) * 100 / len(attempts))
        if attempts
        else 0,
        weekly_activity=[
            {
                "label": (today - timedelta(days=i)).strftime("%a")[0],
                "xp": by_date.get(today - timedelta(days=i), 0),
            }
            for i in reversed(range(7))
        ],
        mastery=mastery,
        strongest_topics=[],
        needs_review=[],
    )


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    users = db.execute(
        select(User, func.coalesce(func.sum(XpTransaction.amount), 0).label("xp"))
        .outerjoin(XpTransaction, XpTransaction.user_id == User.id)
        .where(User.is_active.is_(True), User.role == "student")
        .group_by(User.id)
        .order_by(func.coalesce(func.sum(XpTransaction.amount), 0).desc(), User.created_at, User.id)
        .limit(50)
    ).all()
    activity_rows = db.execute(
        select(DailyActivity.user_id, DailyActivity.local_date)
        .join(User, User.id == DailyActivity.user_id)
        .where(
            User.is_active.is_(True),
            User.role == "student",
            DailyActivity.xp_earned > 0,
        )
        .order_by(DailyActivity.user_id, DailyActivity.local_date.desc())
    ).all()
    activity_by_user: dict[UUID, list] = {}
    for user_id, activity_date in activity_rows:
        activity_by_user.setdefault(user_id, []).append(activity_date)

    def streak_for(student: User) -> int:
        dates = activity_by_user.get(student.id, [])
        if not dates:
            return 0
        today = local_today(student)
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

    return [
        LeaderboardEntry(
            rank=index,
            name=student.full_name.split()[0],
            xp=xp,
            streak=streak_for(student),
        )
        for index, (student, xp) in enumerate(users, start=1)
    ]


def _validate_lesson_for_approval(lesson: Lesson, reviewer: User) -> None:
    if lesson.source_reference:
        try:
            validate_source_locator(lesson.source_reference)
        except ValueError as error:
            raise HTTPException(
                status_code=409,
                detail="Cite a page, section, strand or sub-strand before approval",
            ) from error
    if not lesson.explanation_sections:
        raise HTTPException(
            status_code=409, detail="Lesson explanation sections are required"
        )
    if not lesson.questions:
        raise HTTPException(
            status_code=409, detail="Questions are required"
        )
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
        raise HTTPException(
            status_code=409, detail="Every question needs a valid answer format"
        )
    if lesson.author and lesson.author.casefold() == reviewer.email.casefold():
        raise HTTPException(
            status_code=409, detail="A different reviewer must approve the lesson"
        )


def _apply_lesson_status_transition(
    lesson: Lesson,
    next_status: str,
    reviewer: User | None = None,
) -> None:
    transitions = {
        "draft": {"in_review"},
        "in_review": {"draft", "approved"},
        "approved": {"in_review", "published"},
        "published": {"archived"},
        "archived": {"draft"},
    }
    if next_status not in transitions.get(lesson.content_status, set()):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot move lesson from {lesson.content_status} to {next_status}",
        )

    now = datetime.now(UTC)
    if next_status == "approved":
        if reviewer is None:
            raise HTTPException(status_code=409, detail="A reviewer is required to approve lessons")
        _validate_lesson_for_approval(lesson, reviewer)
        lesson.reviewer = reviewer.email
        lesson.reviewed_at = now

    if next_status == "published" and not lesson.reviewed_at:
        raise HTTPException(status_code=409, detail="Lesson must be reviewed before publishing")
    if next_status in {"draft", "in_review"}:
        lesson.reviewer = None
        lesson.reviewed_at = None
    lesson.content_status = next_status
    lesson.published = next_status == "published"
    if next_status == "published":
        lesson.published_at = now
    elif next_status == "archived":
        lesson.published_at = lesson.published_at or now


@router.get("/admin/lessons/bulk-publish-preview")
def bulk_publish_preview(
    db: Session = Depends(get_db),
    reviewer: User = Depends(admin_user),
):
    lessons = db.scalars(
        select(Lesson)
        .options(joinedload(Lesson.topic).joinedload(Topic.subject), selectinload(Lesson.questions))
        .where(Lesson.published.is_(False))
        .order_by(Lesson.topic_id, Lesson.sort_order, Lesson.title)
    ).all()
    eligible: list[str] = []
    blocked: list[dict[str, str]] = []
    for lesson in lessons:
        if lesson.content_status == "published":
            continue
        try:
            _validate_lesson_for_approval(lesson, reviewer)
        except HTTPException as exc:
            blocked.append({"id": lesson.slug, "title": lesson.title, "reason": exc.detail})
            continue
        eligible.append(lesson.slug)
    return {
        "eligible_count": len(eligible),
        "blocked_count": len(blocked),
        "eligible": eligible,
        "blocked": blocked,
    }


@router.post("/admin/lessons/bulk-publish")
def bulk_publish_lessons(
    db: Session = Depends(get_db),
    reviewer: User = Depends(admin_user),
):
    lessons = db.scalars(
        select(Lesson)
        .options(joinedload(Lesson.topic).joinedload(Topic.subject), selectinload(Lesson.questions))
        .where(Lesson.published.is_(False))
        .order_by(Lesson.topic_id, Lesson.sort_order, Lesson.title)
    ).all()
    processed: list[str] = []
    skipped: list[str] = []
    blocked: list[dict[str, str]] = []
    for lesson in lessons:
        if lesson.published:
            continue
        try:
            _validate_lesson_for_approval(lesson, reviewer)
            if lesson.content_status == "draft":
                _apply_lesson_status_transition(lesson, "in_review", reviewer)
            if lesson.content_status in {"in_review", "draft"}:
                _apply_lesson_status_transition(lesson, "approved", reviewer)
            if lesson.content_status != "published":
                _apply_lesson_status_transition(lesson, "published", reviewer)
        except HTTPException as exc:
            blocked.append({"id": lesson.slug, "title": lesson.title, "reason": exc.detail})
            continue
        processed.append(lesson.slug)
    db.commit()
    return {
        "processed_count": len(processed),
        "processed": processed,
        "skipped_count": len(skipped),
        "skipped": skipped,
        "blocked_count": len(blocked),
        "blocked": blocked,
    }


@router.patch("/admin/lessons/{lesson_id}/status")
def update_lesson_status(
    lesson_id: str,
    payload: ContentStatusUpdate,
    db: Session = Depends(get_db),
    reviewer: User = Depends(admin_user),
):
    lesson = db.scalar(select(Lesson).where(Lesson.slug == lesson_id).with_for_update())
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    _apply_lesson_status_transition(lesson, payload.status, reviewer)
    db.commit()
    return {
        "id": lesson.slug,
        "status": lesson.content_status,
        "published": lesson.published,
        "reviewer": lesson.reviewer,
        "reviewed_at": lesson.reviewed_at,
        "published_at": lesson.published_at,
        "curriculum_alignment": _curriculum_alignment_status(lesson),
        "quality_status": _quality_status(lesson),
    }
