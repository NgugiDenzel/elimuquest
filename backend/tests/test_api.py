from datetime import timedelta
from pathlib import Path

import pytest
from conftest import TestSession
from sqlalchemy import select

from app.api.v1.router import _answer_matches
from app.content.importer import ContentImportError, import_content
from app.content.schema import ContentPackage
from app.curriculum.catalog import LEVELS
from app.models import (
    Achievement,
    AnswerAttempt,
    DailyActivity,
    Lesson,
    LessonProgress,
    LessonQuestion,
    LessonSession,
    Subject,
    Topic,
    User,
    UserAchievement,
    XpTransaction,
)
from app.services.learning import local_today

MATH_PACKAGE_DIR = (
    Path(__file__).resolve().parents[1] / "content-packages" / "math-curriculum-draft"
)
GRADE6_BOOK_PACKAGE = (
    Path(__file__).resolve().parents[1]
    / "content-packages"
    / "grade6-whole-numbers-pupils-book.json"
)


def seed_lesson():
    with TestSession.begin() as db:
        subject = Subject(
            slug="biology",
            name="Biology",
            code="BIO",
            accent="#34A853",
            icon="🧬",
            curriculum_system="8_4_4",
            curriculum_level="Form 4",
            source_id="KICD-844",
        )
        db.add(subject)
        db.flush()
        topic = Topic(subject_id=subject.id, slug="cells", name="Cell biology")
        db.add(topic)
        db.flush()
        lesson = Lesson(
            topic_id=topic.id,
            slug="cell-structure",
            title="Cell Structure",
            description="Demo lesson",
            content="Fictional demonstration content.",
            published=True,
            content_status="published",
            learning_objectives=["Identify a cell structure."],
            explanation_sections=[{"title": "Overview", "body": "An original example."}],
            worked_examples=[{"prompt": "Example", "solution": "Example solution."}],
            source_id="KICD-844",
            source_reference="KICD test reference, p. 1.",
            author="author@example.test",
        )
        hidden = Lesson(
            topic_id=topic.id,
            slug="unpublished",
            title="Draft",
            description="Draft",
            content="Not published",
            published=False,
            content_status="draft",
            learning_objectives=["Explain a simple example."],
            explanation_sections=[{"title": "Overview", "body": "Original example text."}],
            worked_examples=[{"prompt": "Example", "solution": "Solution", "reasoning": "Reason"}],
            source_id="KICD-844",
            source_reference="KICD test reference, p. 1.",
            author="author@example.test",
        )
        db.add_all([lesson, hidden])
        db.flush()
        db.add_all(
            [
                LessonQuestion(
                    lesson_id=lesson.id,
                    prompt="Which organelle?",
                    options=["Nucleus", "Cell wall"],
                    correct_answer="Nucleus",
                    explanation="The nucleus stores genetic material.",
                ),
                LessonQuestion(
                    lesson_id=lesson.id,
                    prompt="Which process?",
                    options=["Respiration", "Evaporation"],
                    correct_answer="Respiration",
                    explanation="Cells release energy through respiration.",
                    sort_order=1,
                ),
            ]
        )
        db.add(
            LessonQuestion(
                lesson_id=hidden.id,
                prompt="Draft question?",
                options=["Answer A", "Answer B"],
                correct_answer="Answer A",
                explanation="A test-only explanation.",
            )
        )
        db.add(
            Achievement(slug="first", name="First", description="First lesson", lesson_threshold=1)
        )


def test_health_readiness_and_auth_required(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/readiness").json() == {"status": "ready"}
    assert client.get("/api/v1/dashboard").status_code == 401
    cors_preflight = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:8081",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert cors_preflight.status_code == 200
    assert cors_preflight.headers["access-control-allow-origin"] == "http://localhost:8081"


def test_registration_role_profile_and_admin_protection(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "one@example.com",
            "password": "strong-password-123",
            "full_name": "Student One",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "student"
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "one@example.com", "password": "strong-password-123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/me", headers=headers).status_code == 200
    assert client.get("/api/v1/admin/lessons", headers=headers).status_code == 403


def test_published_lesson_answers_and_idempotent_completion(client, student_headers):
    seed_lesson()
    assert client.get("/api/v1/lessons/unpublished", headers=student_headers).status_code == 404
    lesson = client.get("/api/v1/lessons/cell-structure", headers=student_headers).json()
    assert "correct_answer" not in str(lesson)
    started = client.post(
        "/api/v1/lesson-sessions",
        headers=student_headers,
        json={"lesson_id": "cell-structure"},
    )
    assert started.status_code == 201
    session_id = started.json()["id"]
    questions = started.json()["lesson"]["questions"]
    first = client.post(
        f"/api/v1/lesson-sessions/{session_id}/answers",
        headers=student_headers,
        json={"question_id": questions[0]["id"], "answer": "nucleus"},
    )
    assert first.status_code == 200
    assert first.json()["correct"] is True
    assert (
        client.post(
            f"/api/v1/lesson-sessions/{session_id}/answers",
            headers=student_headers,
            json={"question_id": questions[0]["id"], "answer": "Nucleus"},
        ).status_code
        == 409
    )
    second = client.post(
        f"/api/v1/lesson-sessions/{session_id}/answers",
        headers=student_headers,
        json={"question_id": questions[1]["id"], "answer": "wrong"},
    )
    assert second.json()["correct"] is False
    completed = client.post(
        f"/api/v1/lesson-sessions/{session_id}/complete", headers=student_headers
    )
    assert completed.status_code == 200
    assert completed.json()["score_percent"] == 50
    assert completed.json()["xp_awarded"] == 15
    duplicate = client.post(
        f"/api/v1/lesson-sessions/{session_id}/complete", headers=student_headers
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["already_completed"] is True
    with TestSession() as db:
        assert len(db.scalars(select(XpTransaction)).all()) == 1
        assert len(db.scalars(select(LessonProgress)).all()) == 1
        assert len(db.scalars(select(Achievement)).all()) == 1
        assert len(db.scalars(select(UserAchievement)).all()) == 1
    assert client.get("/api/v1/dashboard", headers=student_headers).json()["total_xp"] == 15


def test_answer_submission_validates_input_and_rejects_incomplete_completion(
    client, student_headers
):
    seed_lesson()
    started = client.post(
        "/api/v1/lesson-sessions",
        headers=student_headers,
        json={"lesson_id": "cell-structure"},
    )
    assert started.status_code == 201
    session_id = started.json()["id"]
    question_id = started.json()["lesson"]["questions"][0]["id"]

    empty_answer = client.post(
        f"/api/v1/lesson-sessions/{session_id}/answers",
        headers=student_headers,
        json={"question_id": question_id, "answer": ""},
    )
    assert empty_answer.status_code == 422

    unknown_question = client.post(
        f"/api/v1/lesson-sessions/{session_id}/answers",
        headers=student_headers,
        json={
            "question_id": "00000000-0000-0000-0000-000000000000",
            "answer": "response",
        },
    )
    assert unknown_question.status_code == 404

    incomplete = client.post(
        f"/api/v1/lesson-sessions/{session_id}/complete",
        headers=student_headers,
    )
    assert incomplete.status_code == 409
    assert incomplete.json()["detail"] == "Answer every question before completing the lesson"

    submitted = client.post(
        f"/api/v1/lesson-sessions/{session_id}/answers",
        headers=student_headers,
        json={"question_id": question_id, "answer": "nucleus"},
    )
    assert submitted.status_code == 200
    still_incomplete = client.post(
        f"/api/v1/lesson-sessions/{session_id}/complete",
        headers=student_headers,
    )
    assert still_incomplete.status_code == 409

    with TestSession() as db:
        assert len(db.scalars(select(AnswerAttempt)).all()) == 1
        assert db.scalars(select(LessonProgress)).all() == []
        assert db.scalars(select(XpTransaction)).all() == []


def test_session_data_isolation(client, student_headers):
    seed_lesson()
    started = client.post(
        "/api/v1/lesson-sessions",
        headers=student_headers,
        json={"lesson_id": "cell-structure"},
    )
    session_id = started.json()["id"]
    other = client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "password": "strong-password-456",
            "full_name": "Other Student",
        },
    )
    assert other.status_code == 201
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "strong-password-456"},
    ).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {token}"}
    assert (
        client.get(f"/api/v1/lesson-sessions/{session_id}", headers=other_headers).status_code
        == 404
    )


def test_daily_goal_and_consecutive_day_streak(client, student_headers):
    with TestSession() as db:
        user = db.scalar(select(User))
        assert user is not None
        today = local_today(user)
        db.add_all(
            [
                DailyActivity(user_id=user.id, local_date=today, xp_earned=7, lessons_completed=1),
                DailyActivity(
                    user_id=user.id,
                    local_date=today - timedelta(days=1),
                    xp_earned=12,
                    lessons_completed=1,
                ),
            ]
        )
        db.commit()
    response = client.get("/api/v1/dashboard", headers=student_headers)
    assert response.status_code == 200
    assert response.json()["streak_days"] == 2
    assert response.json()["daily_progress_xp"] == 7


@pytest.mark.parametrize(
    ("correct_answer", "answer", "expected"),
    [
        ("68,005", "68005", True),
        ("68,005", "68 005", True),
        ("100,000", "1,00,000", False),
        ("100,000", "100,00", False),
        ("13", " 13. ", True),
        (
            "ninety-seven thousand, five hundred and thirty",
            "NINETY SEVEN THOUSAND FIVE HUNDRED AND THIRTY!",
            True,
        ),
        (
            "ninety-seven thousand, five hundred and thirty",
            "ninety-seven thousand, five hundred and thirty-one",
            False,
        ),
    ],
)
def test_short_answer_normalization_only_accepts_equivalent_values(
    correct_answer, answer, expected
):
    question = LessonQuestion(question_type="short_answer", correct_answer=correct_answer)
    assert _answer_matches(question, answer) is expected


def test_admin_can_review_unpublished_content(client, student_headers):
    seed_lesson()
    assert client.get("/api/v1/admin/lessons", headers=student_headers).status_code == 403
    with TestSession() as db:
        user = db.scalar(select(User))
        assert user is not None
        user.role = "admin"
        db.commit()
    token = student_headers["Authorization"].removeprefix("Bearer ")
    response = client.get(
        "/api/v1/admin/lessons",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert any(item["published"] is False for item in response.json()["items"])


def seed_curriculum_catalog():
    with TestSession.begin() as db:
        for level in LEVELS:
            for definition in level.subjects:
                db.add(
                    Subject(
                        slug=definition.slug,
                        name=definition.name,
                        code=definition.code,
                        description=definition.description,
                        accent=definition.accent,
                        icon=definition.icon,
                        curriculum_system=level.system,
                        curriculum_level=level.level,
                        curriculum_version=level.version,
                        source_id=definition.source_id,
                        is_demo=False,
                    )
                )


def test_curriculum_subjects_and_content_are_level_scoped(client, student_headers):
    seed_curriculum_catalog()
    options = client.get("/api/v1/curricula", headers=student_headers).json()["items"]
    grade_nine = next(item for item in options if item["level"] == "Grade 9")
    assert [item["name"] for item in grade_nine["subjects"]] == [
        "Mathematics",
        "English",
        "Kiswahili",
        "Integrated Science",
    ]
    form_four_names = {
        item["name"] for item in client.get("/api/v1/subjects", headers=student_headers).json()
    }
    assert form_four_names == {"Mathematics", "English", "Kiswahili", "Chemistry", "Physics"}
    selected = client.patch(
        "/api/v1/me/profile",
        headers=student_headers,
        json={"curriculum_system": "CBC_CBE", "curriculum_level": "Grade 9"},
    )
    assert selected.status_code == 200
    assert selected.json()["form"] == "Grade 9"
    grade_nine_subjects = client.get("/api/v1/subjects", headers=student_headers).json()
    assert {item["name"] for item in grade_nine_subjects} == {
        "Mathematics",
        "English",
        "Kiswahili",
        "Integrated Science",
    }
    assert (
        client.get("/api/v1/subjects/chemistry-form-4", headers=student_headers).status_code == 404
    )
    science = next(item for item in grade_nine_subjects if item["name"] == "Integrated Science")
    assert science["ready"] is False
    assert science["lessons"] == 0
    selected = client.patch(
        "/api/v1/me/profile",
        headers=student_headers,
        json={"curriculum_system": "CBC_CBE", "curriculum_level": "Grade 6"},
    )
    assert selected.status_code == 200
    grade_six_subjects = client.get("/api/v1/subjects", headers=student_headers).json()
    assert {item["name"] for item in grade_six_subjects} == {
        "Mathematics",
        "English",
        "Kiswahili",
        "Science & Technology",
    }
    assert not {"Chemistry", "Physics"}.intersection(item["name"] for item in grade_six_subjects)
    invalid = client.patch(
        "/api/v1/me/profile",
        headers=student_headers,
        json={"curriculum_system": "CBC_CBE", "curriculum_level": "Form 4"},
    )
    assert invalid.status_code == 422


def test_learning_path_returns_all_published_subject_lessons(client, student_headers):
    seed_curriculum_catalog()
    selected = client.patch(
        "/api/v1/me/profile",
        headers=student_headers,
        json={"curriculum_system": "CBC_CBE", "curriculum_level": "Grade 6"},
    )
    assert selected.status_code == 200
    with TestSession.begin() as db:
        subject = db.scalar(select(Subject).where(Subject.slug == "english-grade-6"))
        assert subject is not None
        topic = Topic(subject_id=subject.id, slug="coverage-test", name="Coverage test")
        db.add(topic)
        db.flush()
        lessons = [
            Lesson(
                topic_id=topic.id,
                slug=f"coverage-test-{index}",
                title=f"Coverage lesson {index}",
                description="Published lesson for list completeness regression.",
                content_status="published",
                published=True,
                learning_objectives=["Explain a testable idea."],
                explanation_sections=[{"title": "Explanation", "body": "Lesson content."}],
            )
            for index in range(5)
        ]
        db.add_all(lessons)
        db.flush()
        db.add_all(
            [
                LessonQuestion(
                    lesson_id=lesson.id,
                    prompt=f"Coverage question {index}?",
                    options=["Correct", "Incorrect"],
                    correct_answer="Correct",
                    explanation="The correct option is identified in the lesson.",
                )
                for index, lesson in enumerate(lessons)
            ]
        )

    learning_path = client.get(
        "/api/v1/subjects/english-grade-6/learning-path",
        headers=student_headers,
    )

    assert learning_path.status_code == 200
    assert len(learning_path.json()["lessons"]) == 5
    assert all(item["questions_count"] == 1 for item in learning_path.json()["lessons"])
    assert (
        client.get("/api/v1/lessons/coverage-test-0", headers=student_headers).status_code
        == 200
    )


def test_admin_review_workflow_controls_publication(client, student_headers):
    seed_lesson()
    forbidden = client.patch(
        "/api/v1/admin/lessons/unpublished/status",
        headers=student_headers,
        json={"status": "in_review"},
    )
    assert forbidden.status_code == 403
    with TestSession() as db:
        user = db.scalar(select(User))
        assert user is not None
        user.role = "admin"
        db.commit()
    headers = student_headers
    assert (
        client.patch(
            "/api/v1/admin/lessons/unpublished/status",
            headers=headers,
            json={"status": "approved"},
        ).status_code
        == 409
    )
    assert (
        client.patch(
            "/api/v1/admin/lessons/unpublished/status",
            headers=headers,
            json={"status": "in_review"},
        ).status_code
        == 200
    )
    approved = client.patch(
        "/api/v1/admin/lessons/unpublished/status",
        headers=headers,
        json={"status": "approved"},
    )
    assert approved.status_code == 200
    published = client.patch(
        "/api/v1/admin/lessons/unpublished/status",
        headers=headers,
        json={"status": "published"},
    )
    assert published.status_code == 200
    assert published.json()["published"] is True
    assert client.get("/api/v1/lessons/unpublished", headers=headers).status_code == 200


def test_admin_bulk_publish_handles_eligible_drafts(client, student_headers):
    seed_lesson()
    with TestSession() as db:
        user = db.scalar(select(User))
        assert user is not None
        user.role = "admin"
        db.commit()
    response = client.post(
        "/api/v1/admin/lessons/bulk-publish",
        headers=student_headers,
    )
    assert response.status_code == 200
    assert response.json()["processed_count"] == 1
    assert response.json()["processed"] == ["unpublished"]
    assert client.get("/api/v1/lessons/unpublished", headers=student_headers).status_code == 200


def test_admin_bulk_publish_leaves_blocked_drafts_unchanged(client, student_headers):
    seed_lesson()
    with TestSession.begin() as db:
        topic = db.scalar(select(Topic).where(Topic.slug == "cells"))
        assert topic is not None
        db.add(
            Lesson(
                topic_id=topic.id,
                slug="blocked-draft",
                title="Blocked draft",
                description="Missing required explanation sections.",
                content_status="draft",
                published=False,
                explanation_sections=[],
                author="author@example.test",
            )
        )
        user = db.scalar(select(User))
        assert user is not None
        user.role = "admin"

    response = client.post(
        "/api/v1/admin/lessons/bulk-publish",
        headers=student_headers,
    )

    assert response.status_code == 200
    assert response.json()["processed"] == ["unpublished"]
    assert response.json()["blocked"] == [
        {
            "id": "blocked-draft",
            "title": "Blocked draft",
            "reason": "Lesson explanation sections are required",
        }
    ]
    with TestSession() as db:
        blocked = db.scalar(select(Lesson).where(Lesson.slug == "blocked-draft"))
        assert blocked is not None
        assert blocked.content_status == "draft"
        assert blocked.published is False


def test_admin_can_publish_content_without_official_kicd_metadata(client, student_headers):
    with TestSession.begin() as db:
        subject = Subject(
            slug="biology",
            name="Biology",
            code="BIO",
            accent="#34A853",
            icon="🧬",
            curriculum_system="8_4_4",
            curriculum_level="Form 4",
            source_id=None,
        )
        db.add(subject)
        db.flush()
        topic = Topic(subject_id=subject.id, slug="research", name="Research notes")
        db.add(topic)
        db.flush()
        lesson = Lesson(
            topic_id=topic.id,
            slug="research-draft",
            title="Research Draft",
            description="A useful lesson without an official KICD citation.",
            content="Credible educational material prepared for review.",
            published=False,
            content_status="draft",
            learning_objectives=["Explain a research-based concept."],
            explanation_sections=[{"title": "Overview", "body": "A clear explanation."}],
            worked_examples=[
                {"prompt": "Example", "solution": "Solution", "reasoning": "Reasoning"}
            ],
            source_id=None,
            source_reference=None,
            author="teacher@example.test",
        )
        db.add(lesson)
        db.flush()
        db.add(
            LessonQuestion(
                lesson_id=lesson.id,
                prompt="What is the main idea?",
                options=["Option A", "Option B"],
                correct_answer="Option A",
                explanation="The lesson explains this carefully.",
            )
        )
        user = db.scalar(select(User))
        assert user is not None
        user.role = "admin"
        db.commit()
    review = client.patch(
        "/api/v1/admin/lessons/research-draft/status",
        headers=student_headers,
        json={"status": "in_review"},
    )
    assert review.status_code == 200
    response = client.patch(
        "/api/v1/admin/lessons/research-draft/status",
        headers=student_headers,
        json={"status": "approved"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    published = client.patch(
        "/api/v1/admin/lessons/research-draft/status",
        headers=student_headers,
        json={"status": "published"},
    )
    assert published.status_code == 200
    assert published.json()["published"] is True


def test_content_import_is_dry_run_idempotent_and_protects_overwrites(client):
    seed_curriculum_catalog()
    package = ContentPackage.model_validate(
        {
            "schema_version": "1.0",
            "curriculum_system": "CBC_CBE",
            "curriculum_level": "Grade 9",
            "curriculum_version": "KICD-G9-2024-07",
            "subject_slug": "integrated-science-grade-9",
            "topic_slug": "schema-fixture",
            "topic_name": "Schema fixture (not curriculum content)",
            "topic_source_reference": "KICD Grade 9 design, p. 1.",
            "source_id": "KICD-G9-DESIGNS",
            "lessons": [
                {
                    "slug": "schema-fixture-lesson",
                    "title": "Schema fixture",
                    "description": "Non-curriculum fixture for importer tests.",
                    "content": "This is test data only and makes no curriculum claims.",
                    "learning_objectives": ["Demonstrate package structure."],
                    "explanation_sections": [
                        {"title": "Fixture", "body": "This content is not for learners."}
                    ],
                    "worked_examples": [
                        {"prompt": "Fixture", "solution": "Fixture", "reasoning": "Fixture"}
                    ],
                    "source_reference": "KICD Grade 9 design, p. 1.",
                    "author": "test-author@example.test",
                    "questions": [
                        {
                            "prompt": "Fixture question?",
                            "options": ["A", "B"],
                            "correct_answer": "A",
                            "explanation": "Fixture explanation.",
                        }
                    ],
                }
            ],
        }
    )
    with TestSession.begin() as db:
        result = import_content(package, db)
        assert result["created"] == 1
        assert db.scalar(select(Lesson).where(Lesson.slug == "schema-fixture-lesson")) is None
    with TestSession.begin() as db:
        result = import_content(package, db, apply=True)
        assert result["created"] == 1
    with TestSession.begin() as db:
        repeated = import_content(package, db, apply=True)
        assert repeated["created"] == 0
        assert repeated["unchanged"] == 1
        lesson = db.scalar(select(Lesson).where(Lesson.slug == "schema-fixture-lesson"))
        assert lesson is not None
        assert lesson.content_status == "draft"
        assert lesson.published is False


def test_math_draft_packages_import_and_complete_reviewed_learner_journey(
    client, student_headers
):
    seed_curriculum_catalog()
    packages = [
        ContentPackage.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(MATH_PACKAGE_DIR.glob("*.json"))
    ]
    assert len(packages) == 36
    expected_counts = {
        "Grade 6": (8, 48),
        "Grade 9": (18, 86),
        "Form 4": (10, 50),
    }
    for level, (lesson_count, question_count) in expected_counts.items():
        level_packages = [package for package in packages if package.curriculum_level == level]
        assert len(level_packages) == lesson_count
        assert sorted(package.lessons[0].sort_order for package in level_packages) == list(
            range(1, lesson_count + 1)
        )
        assert sum(len(package.lessons[0].questions) for package in level_packages) == (
            question_count
        )
    assert sum(
        len(lesson.questions) for package in packages for lesson in package.lessons
    ) == 184
    assert all(
        package.ai_generated is False
        and package.is_demo is False
        and package.topic_source_reference.startswith(
            "ElimuQuest Mathematics Curriculum Draft v1, PDF p"
        )
        and all(
            question.question_type == "short_answer" and not question.options
            for lesson in package.lessons
            for question in lesson.questions
        )
        for package in packages
    )

    conflicting_package = packages[0].model_copy(
        update={"topic_name": f"{packages[0].topic_name} conflict"}
    )
    with pytest.raises(ContentImportError):
        with TestSession.begin() as db:
            import_content(packages[0], db, apply=True)
            import_content(conflicting_package, db, apply=True)
    with TestSession() as db:
        assert db.scalars(select(Lesson)).all() == []
        assert db.scalars(select(Topic)).all() == []

    with TestSession.begin() as db:
        dry_runs = [import_content(package, db) for package in packages]
        assert sum(result["created"] for result in dry_runs) == 36
        assert db.scalars(select(Lesson)).all() == []
        assert db.scalars(select(Topic)).all() == []
    with TestSession.begin() as db:
        results = [import_content(package, db, apply=True) for package in packages]
        assert sum(result["created"] for result in results) == 36
        db.flush()
        assert len(db.scalars(select(Lesson)).all()) == 36
        assert len(db.scalars(select(Topic)).all()) == 36
        assert len(db.scalars(select(LessonQuestion)).all()) == 184
        assert all(
            lesson.content_status == "draft" and lesson.published is False
            for lesson in db.scalars(select(Lesson)).all()
        )
    with TestSession.begin() as db:
        repeated = [import_content(package, db, apply=True) for package in packages]
        assert sum(result["created"] for result in repeated) == 0
        assert sum(result["unchanged"] for result in repeated) == 36
        assert len(db.scalars(select(Lesson)).all()) == 36

    selection = client.patch(
        "/api/v1/me/profile",
        headers=student_headers,
        json={"curriculum_system": "CBC_CBE", "curriculum_level": "Grade 9"},
    )
    assert selection.status_code == 200
    grade_nine_subjects = client.get("/api/v1/subjects", headers=student_headers).json()
    mathematics = next(item for item in grade_nine_subjects if item["name"] == "Mathematics")
    assert mathematics["ready"] is False
    assert mathematics["lessons"] == 0
    assert (
        client.get("/api/v1/lessons/grade-9-integers", headers=student_headers).status_code
        == 404
    )
    assert client.get("/api/v1/admin/lessons", headers=student_headers).status_code == 403
    for system, level, other_lesson in (
        ("CBC_CBE", "Grade 6", "grade-9-integers"),
        ("8_4_4", "Form 4", "grade-6-whole-numbers"),
    ):
        changed = client.patch(
            "/api/v1/me/profile",
            headers=student_headers,
            json={"curriculum_system": system, "curriculum_level": level},
        )
        assert changed.status_code == 200
        assert (
            client.get(
                f"/api/v1/lessons/{other_lesson}", headers=student_headers
            ).status_code
            == 404
        )
    assert client.patch(
        "/api/v1/me/profile",
        headers=student_headers,
        json={"curriculum_system": "CBC_CBE", "curriculum_level": "Grade 9"},
    ).status_code == 200

    with TestSession.begin() as db:
        user = db.scalar(select(User))
        assert user is not None
        user.role = "admin"
    admin_items = client.get("/api/v1/admin/lessons", headers=student_headers)
    assert admin_items.status_code == 200
    assert len(admin_items.json()["items"]) == 36
    for status in ("in_review", "approved", "published"):
        reviewed = client.patch(
            "/api/v1/admin/lessons/grade-9-integers/status",
            headers=student_headers,
            json={"status": status},
        )
        assert reviewed.status_code == 200
    with TestSession.begin() as db:
        user = db.scalar(select(User))
        assert user is not None
        user.role = "student"

    lesson_response = client.get("/api/v1/lessons/grade-9-integers", headers=student_headers)
    assert lesson_response.status_code == 200
    lesson_data = lesson_response.json()
    assert len(lesson_data["questions"]) == 7
    assert all(question["question_type"] == "short_answer" for question in lesson_data["questions"])
    assert "correct_answer" not in str(lesson_data)
    started = client.post(
        "/api/v1/lesson-sessions",
        headers=student_headers,
        json={"lesson_id": "grade-9-integers"},
    )
    assert started.status_code == 201
    session_id = started.json()["id"]
    session_questions = started.json()["lesson"]["questions"]
    first_answer = client.post(
        f"/api/v1/lesson-sessions/{session_id}/answers",
        headers=student_headers,
        json={"question_id": session_questions[0]["id"], "answer": "13"},
    )
    assert first_answer.status_code == 200
    assert first_answer.json()["correct"] is True
    incorrect_answer = client.post(
        f"/api/v1/lesson-sessions/{session_id}/answers",
        headers=student_headers,
        json={"question_id": session_questions[1]["id"], "answer": "−22"},
    )
    assert incorrect_answer.status_code == 200
    assert incorrect_answer.json() == {
        "question_id": session_questions[1]["id"],
        "correct": False,
        "explanation": "Correct answer: −23.",
    }
    integers_package = next(
        package for package in packages if package.lessons[0].slug == "grade-9-integers"
    )
    for index in range(2, len(session_questions)):
        answer = integers_package.lessons[0].questions[index].correct_answer
        if index == 4:
            answer = "-8"
        response = client.post(
            f"/api/v1/lesson-sessions/{session_id}/answers",
            headers=student_headers,
            json={
                "question_id": session_questions[index]["id"],
                "answer": answer,
            },
        )
        assert response.status_code == 200
        assert response.json()["correct"] is True
    completed = client.post(
        f"/api/v1/lesson-sessions/{session_id}/complete", headers=student_headers
    )
    assert completed.status_code == 200
    assert completed.json()["correct_answers"] == 6
    assert completed.json()["score_percent"] == 86
    assert completed.json()["xp_awarded"] == 40
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "student@example.com", "password": "strong-password-123"},
    ).json()["access_token"]
    reauthenticated_headers = {"Authorization": f"Bearer {token}"}
    dashboard = client.get("/api/v1/dashboard", headers=reauthenticated_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_xp"] == 40
    assert dashboard.json()["lessons_completed"] == 1
    duplicate = client.post(
        f"/api/v1/lesson-sessions/{session_id}/complete", headers=reauthenticated_headers
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["already_completed"] is True
    with TestSession() as db:
        assert len(db.scalars(select(XpTransaction)).all()) == 1
        assert len(db.scalars(select(LessonProgress)).all()) == 1


def test_grade_six_whole_numbers_book_quizzes_and_learner_journey(client, student_headers):
    seed_curriculum_catalog()
    package = ContentPackage.model_validate_json(
        GRADE6_BOOK_PACKAGE.read_text(encoding="utf-8")
    )
    assert package.curriculum_system == "CBC_CBE"
    assert package.curriculum_level == "Grade 6"
    assert package.subject_slug == "mathematics-grade-6"
    assert package.topic_name == "Whole Numbers"
    assert [lesson.sort_order for lesson in package.lessons] == [101, 102, 103, 104, 105]
    assert [lesson.title for lesson in package.lessons] == [
        "Step 1: Place value and total value",
        "Step 2: Reading and writing numbers in words",
        "Step 3: Ordering numbers",
        "Step 4: Rounding off to the nearest thousand",
        "Step 5: Squares and square roots",
    ]
    assert [len(lesson.questions) for lesson in package.lessons] == [2, 5, 3, 5, 5]
    assert sum(len(lesson.questions) for lesson in package.lessons) == 20
    assert [
        [question.correct_answer for question in lesson.questions]
        for lesson in package.lessons
    ] == [
        [
            "Hundred thousands; 600,000",
            "Thousands; 2,000",
        ],
        [
            "twenty-three thousand, four hundred and fifty",
            "sixty thousand and eight",
            "68,005",
            "90,412",
            "ninety-seven thousand, five hundred and thirty",
        ],
        [
            "Ksh 4,999; Ksh 45,096; Ksh 45,609; Ksh 54,069",
            "97,530",
            "30,579",
        ],
        ["34,000", "79,000", "97,000", "100,000", "31,000"],
        ["81", "625", "13", "60", "35"],
    ]
    assert all(
        lesson.explanation_sections
        and lesson.source_reference
        and "answer key absent from excerpt" in lesson.source_reference
        and "calculated independently" in lesson.source_reference
        for lesson in package.lessons
    )

    with TestSession.begin() as db:
        dry_run = import_content(package, db)
        assert dry_run["created"] == 5
        assert db.scalars(select(Lesson)).all() == []
    with TestSession.begin() as db:
        imported = import_content(package, db, apply=True)
        assert imported["created"] == 5
        db.flush()
        lessons = db.scalars(select(Lesson).order_by(Lesson.sort_order)).all()
        assert len(lessons) == 5
        assert sum(len(lesson.questions) for lesson in lessons) == 20
        assert all(lesson.content_status == "draft" and not lesson.published for lesson in lessons)
    with TestSession.begin() as db:
        repeated = import_content(package, db, apply=True)
        assert repeated["created"] == 0
        assert repeated["unchanged"] == 5
        assert len(db.scalars(select(Lesson)).all()) == 5

    selected = client.patch(
        "/api/v1/me/profile",
        headers=student_headers,
        json={"curriculum_system": "CBC_CBE", "curriculum_level": "Grade 6"},
    )
    assert selected.status_code == 200
    math_subject = next(
        subject
        for subject in client.get("/api/v1/subjects", headers=student_headers).json()
        if subject["id"] == "mathematics-grade-6"
    )
    assert math_subject["ready"] is False
    assert math_subject["lessons"] == 0
    assert (
        client.get(
            f"/api/v1/lessons/{package.lessons[0].slug}", headers=student_headers
        ).status_code
        == 404
    )
    assert client.get("/api/v1/admin/lessons", headers=student_headers).status_code == 403

    with TestSession.begin() as db:
        user = db.scalar(select(User))
        assert user is not None
        user.role = "admin"
    admin_review = client.get("/api/v1/admin/lessons", headers=student_headers)
    assert admin_review.status_code == 200
    book_slugs = {lesson.slug for lesson in package.lessons}
    reviewed_lessons = [
        item for item in admin_review.json()["items"] if item["id"] in book_slugs
    ]
    assert [item["id"] for item in reviewed_lessons] == [
        lesson.slug for lesson in package.lessons
    ]
    assert all(
        item["status"] == "draft"
        and item["source_reference"]
        and "answer key absent from excerpt" in item["source_reference"]
        and "calculated independently" in item["source_reference"]
        and item["explanation_sections"][0]["body"]
        and len(item["questions"]) == len(
            next(lesson for lesson in package.lessons if lesson.slug == item["id"]).questions
        )
        for item in reviewed_lessons
    )
    for lesson_package in package.lessons:
        for status in ("in_review", "approved", "published"):
            response = client.patch(
                f"/api/v1/admin/lessons/{lesson_package.slug}/status",
                headers=student_headers,
                json={"status": status},
            )
            assert response.status_code == 200
    with TestSession.begin() as db:
        user = db.scalar(select(User))
        assert user is not None
        user.role = "student"

    path = client.get(
        "/api/v1/subjects/mathematics-grade-6/learning-path",
        headers=student_headers,
    )
    assert path.status_code == 200
    assert [lesson["id"] for lesson in path.json()["lessons"]] == [
        lesson.slug for lesson in package.lessons
    ]
    assert [lesson["title"] for lesson in path.json()["lessons"]] == [
        lesson.title for lesson in package.lessons
    ]
    subject_after_review = client.get(
        "/api/v1/subjects/mathematics-grade-6", headers=student_headers
    ).json()
    assert subject_after_review["ready"] is True
    assert subject_after_review["lessons"] == 5

    session_ids = []
    first_attempt_xp = 0
    for lesson_package in package.lessons:
        detail = client.get(
            f"/api/v1/lessons/{lesson_package.slug}", headers=student_headers
        )
        assert detail.status_code == 200
        assert len(detail.json()["questions"]) == len(lesson_package.questions)
        assert "correct_answer" not in detail.text
        assert lesson_package.explanation_sections[0].body in detail.json()[
            "explanation_sections"
        ][0]["body"]
        started = client.post(
            "/api/v1/lesson-sessions",
            headers=student_headers,
            json={"lesson_id": lesson_package.slug},
        )
        assert started.status_code == 201
        session_id = started.json()["id"]
        session_ids.append(session_id)
        questions = started.json()["lesson"]["questions"]
        correct_count = 0
        for index, (question_package, question) in enumerate(
            zip(lesson_package.questions, questions, strict=True)
        ):
            if index == 0:
                answer = (
                    question_package.options[-1]
                    if question_package.question_type == "multiple_choice"
                    else "not the answer"
                )
                if answer == question_package.correct_answer:
                    answer = question_package.options[0]
            else:
                answer = question_package.correct_answer
                if question_package.question_type == "short_answer":
                    answer = answer.replace(",", "").replace("-", "  ").upper()
            submitted = client.post(
                f"/api/v1/lesson-sessions/{session_id}/answers",
                headers=student_headers,
                json={"question_id": question["id"], "answer": answer},
            )
            assert submitted.status_code == 200
            assert submitted.json()["correct"] is (index != 0)
            if index == 0 and question_package.question_type == "short_answer":
                assert submitted.json()["explanation"] == (
                    f"Correct answer: {question_package.correct_answer}"
                )
            correct_count += int(submitted.json()["correct"])

        completed = client.post(
            f"/api/v1/lesson-sessions/{session_id}/complete",
            headers=student_headers,
        )
        question_count = len(lesson_package.questions)
        expected_xp = 10 + correct_count * 5
        first_attempt_xp += expected_xp
        assert completed.status_code == 200
        assert completed.json()["correct_answers"] == question_count - 1
        assert completed.json()["score_percent"] == round(
            (question_count - 1) * 100 / question_count
        )
        assert completed.json()["xp_awarded"] == expected_xp
        duplicate = client.post(
            f"/api/v1/lesson-sessions/{session_id}/complete",
            headers=student_headers,
        )
        assert duplicate.status_code == 200
        assert duplicate.json()["already_completed"] is True
        assert duplicate.json()["xp_awarded"] == expected_xp

    first_lesson = package.lessons[0]
    retry = client.post(
        "/api/v1/lesson-sessions",
        headers=student_headers,
        json={"lesson_id": first_lesson.slug},
    )
    assert retry.status_code == 201
    retry_session_id = retry.json()["id"]
    for question_package, question in zip(
        first_lesson.questions, retry.json()["lesson"]["questions"], strict=True
    ):
        answer = question_package.correct_answer
        if question_package.question_type == "short_answer":
            answer = answer.replace(",", "").replace("-", " ")
        result = client.post(
            f"/api/v1/lesson-sessions/{retry_session_id}/answers",
            headers=student_headers,
            json={"question_id": question["id"], "answer": answer},
        )
        assert result.status_code == 200
        assert result.json()["correct"] is True
    retry_result = client.post(
        f"/api/v1/lesson-sessions/{retry_session_id}/complete",
        headers=student_headers,
    )
    retry_xp = 10 + len(first_lesson.questions) * 5
    assert retry_result.status_code == 200
    assert retry_result.json()["score_percent"] == 100
    assert retry_result.json()["xp_awarded"] == retry_xp

    token = client.post(
        "/api/v1/auth/login",
        json={"email": "student@example.com", "password": "strong-password-123"},
    ).json()["access_token"]
    reauthenticated = {"Authorization": f"Bearer {token}"}
    dashboard = client.get("/api/v1/dashboard", headers=reauthenticated)
    assert dashboard.status_code == 200
    assert dashboard.json()["lessons_completed"] == 5
    assert dashboard.json()["total_xp"] == first_attempt_xp + retry_xp
    persisted_path = client.get(
        "/api/v1/subjects/mathematics-grade-6/learning-path",
        headers=reauthenticated,
    ).json()
    assert all(lesson["completed"] for lesson in persisted_path["lessons"])
    with TestSession() as db:
        progress = db.scalars(select(LessonProgress)).all()
        transactions = db.scalars(select(XpTransaction)).all()
        assert len(progress) == 5
        assert len(transactions) == 6
        assert sorted(item.attempts for item in progress) == [1, 1, 1, 1, 2]
        assert len(db.scalars(select(LessonSession)).all()) == 6
