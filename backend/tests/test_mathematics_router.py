import json
from pathlib import Path

import pytest
from conftest import TestSession

from app.core.security import create_access_token
from app.models import User
from app.services import mathematics as mathematics_service
from app.services.mathematics_coverage import _register

MATHEMATICS_PATHS = {
    "/api/v1/mathematics/curriculum": {"get"},
    "/api/v1/mathematics/coverage": {"get"},
    "/api/v1/mathematics/coverage/validation": {"get"},
    "/api/v1/mathematics/coverage/questions/quality": {"get"},
    "/api/v1/admin/mathematics/number-systems/review": {"get"},
    "/api/v1/admin/mathematics/number-systems/review-decisions": {"post"},
    "/api/v1/mathematics/feedback": {"post"},
    "/api/v1/admin/mathematics/number-systems/feedback": {"get"},
    "/api/v1/mathematics/lessons/{lesson_id}": {"get"},
    "/api/v1/mathematics/lessons/{lesson_id}/answers": {"post"},
}
MATHEMATICS_JSON_FILES = (
    "mathematics-learning-pack.json",
    "mathematics-learning-sequences.json",
    "mathematics-number-systems-phase-b.json",
    "mathematics-number-systems-assessment-phase-b.json",
    "mathematics-curriculum-register.json",
)


def test_mathematics_router_registers_all_existing_paths_and_methods(client):
    paths = client.get("/openapi.json").json()["paths"]
    actual = {
        path: {method for method in operations if method in {"get", "post"}}
        for path, operations in paths.items()
        if "mathematics" in path
    }

    assert actual == MATHEMATICS_PATHS


def test_mathematics_curriculum_and_lesson_routes_remain_public(client):
    response = client.get("/api/v1/mathematics/curriculum")

    assert response.status_code == 200
    assert response.json()["total_lessons"] == 31
    assert response.json()["total_questions"] == 257
    lesson = client.get("/api/v1/mathematics/lessons/math-number-systems-intro")
    assert lesson.status_code == 200
    assert lesson.json()["id"] == "math-number-systems-intro"


def test_mathematics_runtime_content_and_docker_inputs_are_complete(client):
    content_dir = Path(__file__).resolve().parents[1] / "content-packages"
    documents = {
        name: json.loads((content_dir / name).read_text(encoding="utf-8"))
        for name in MATHEMATICS_JSON_FILES
    }
    assert len(documents["mathematics-curriculum-register.json"]["topic_profiles"]) == 20

    dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(
        encoding="utf-8"
    )
    assert all(
        f"COPY content-packages/{name} ./content-packages/" in dockerfile
        for name in MATHEMATICS_JSON_FILES
    )
    assert "USER 10001:10001" in dockerfile

    curriculum = mathematics_service._curriculum()
    lessons = [
        lesson
        for level in curriculum["levels"]
        for unit in level["units"]
        for lesson in unit["lessons"]
    ]
    questions = [question for lesson in lessons for question in lesson["questions"]]
    assert len(lessons) == 31
    assert len({lesson["id"] for lesson in lessons}) == len(lessons)
    assert len(questions) == 257
    assert len({question["id"] for question in questions}) == len(questions)

    registered_topics = set(_register()["topic_profiles"])
    linked_questions = [question for question in questions if question.get("topic_id")]
    unlinked_questions = [question for question in questions if not question.get("topic_id")]
    assert linked_questions
    assert all(question["topic_id"] in registered_topics for question in linked_questions)
    assert all(question.get("learning_objective_ids") for question in linked_questions)
    assert unlinked_questions


def test_mathematics_coverage_rejects_unknown_topics(client):
    response = client.get("/api/v1/mathematics/coverage?unit_id=unknown-unit")

    assert response.status_code == 422
    assert response.json()["detail"] == "Unknown Mathematics unit_id"


def test_mathematics_reports_and_guest_answer_endpoints(client):
    coverage = client.get("/api/v1/mathematics/coverage")
    assert coverage.status_code == 200
    assert client.get("/api/v1/mathematics/coverage/validation").status_code == 200
    assert client.get("/api/v1/mathematics/coverage/questions/quality").status_code == 200

    lesson_id = "math-number-systems-intro"
    lesson = client.get(f"/api/v1/mathematics/lessons/{lesson_id}").json()
    answer_response = client.post(
        f"/api/v1/mathematics/lessons/{lesson_id}/answers",
        json={
            "question_id": lesson["questions"][0]["id"],
            "answer": "not-the-answer",
        },
    )

    assert answer_response.status_code == 200
    assert answer_response.json()["correct"] is False


def test_learner_feedback_preserves_guest_and_authenticated_access(client, student_headers):
    payload = {
        "lesson_id": "math-number-systems-intro",
        "question_id": "math-numbers-q1",
        "category": "general",
        "message": "Synthetic test feedback",
    }

    assert client.post("/api/v1/mathematics/feedback", json=payload).status_code == 201
    assert (
        client.post(
            "/api/v1/mathematics/feedback",
            json=payload,
            headers={"Authorization": "Bearer invalid"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/mathematics/feedback",
            json=payload,
            headers=student_headers,
        ).status_code
        == 201
    )


def test_mathematics_admin_routes_require_admin_authorization(client, student_headers):
    review_path = "/api/v1/admin/mathematics/number-systems/review"
    feedback_path = "/api/v1/admin/mathematics/number-systems/feedback"
    decision_path = "/api/v1/admin/mathematics/number-systems/review-decisions"
    decision = {
        "item_type": "topic",
        "item_id": "number-systems/integers",
        "decision": "approved",
        "comments": "",
        "correction": "",
        "mathematical_error_flag": False,
    }

    assert client.get(review_path).status_code == 401
    assert client.get(feedback_path).status_code == 401
    assert client.post(decision_path, json=decision).status_code == 401
    assert client.get(review_path, headers=student_headers).status_code == 403
    assert client.get(feedback_path, headers=student_headers).status_code == 403
    assert (
        client.post(decision_path, json=decision, headers=student_headers).status_code
        == 403
    )

    with TestSession() as db:
        admin = User(
            email="math-review-admin@example.test",
            password_hash="synthetic-test-hash",
            full_name="Synthetic Mathematics Reviewer",
            role="admin",
        )
        db.add(admin)
        db.commit()
        admin_headers = {
            "Authorization": f"Bearer {create_access_token(admin.id)}"
        }

    decision_response = client.post(decision_path, json=decision, headers=admin_headers)
    assert decision_response.status_code == 201
    review_response = client.get(review_path, headers=admin_headers)
    assert review_response.status_code == 200
    assert any(
        event["id"] == decision_response.json()["id"]
        for event in review_response.json()["history"]
    )

    feedback_response = client.post(
        "/api/v1/mathematics/feedback",
        json={
            "lesson_id": "math-number-systems-intro",
            "category": "general",
            "message": "Synthetic persisted feedback",
        },
    )
    assert feedback_response.status_code == 201
    inbox_response = client.get(feedback_path, headers=admin_headers)
    assert inbox_response.status_code == 200
    assert any(
        item["id"] == feedback_response.json()["id"]
        and item["submitted_by"] == "guest"
        for item in inbox_response.json()["items"]
    )


def test_missing_mathematics_json_file_fails_explicitly(client, monkeypatch):
    original_open = Path.open
    missing_name = "mathematics-learning-pack.json"

    def open_without_missing_pack(path: Path, *args, **kwargs):
        if path.name == missing_name:
            raise FileNotFoundError(f"Missing Mathematics runtime file: {path.name}")
        return original_open(path, *args, **kwargs)

    mathematics_service._curriculum.cache_clear()
    monkeypatch.setattr(Path, "open", open_without_missing_pack)

    with pytest.raises(FileNotFoundError, match=missing_name):
        client.get("/api/v1/mathematics/curriculum")
