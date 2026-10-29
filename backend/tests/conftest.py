import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app
from app.models import (  # noqa: F401
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

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def client():
    Base.metadata.create_all(test_engine)

    def override_get_db():
        with TestSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def student_headers(client):
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": "student@example.com",
            "password": "strong-password-123",
            "full_name": "Alex Learner",
        },
    )
    assert registered.status_code == 201
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "student@example.com", "password": "strong-password-123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
