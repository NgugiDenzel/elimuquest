from pathlib import Path

from app.db.migration_lock import acquire_migration_lock, release_migration_lock

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_api_startup_migrates_before_serving_requests():
    startup = (BACKEND_DIR / "start.sh").read_text(encoding="utf-8")

    migration = startup.index("alembic upgrade head")
    server = startup.index("exec uvicorn app.main:app")
    assert migration < server


def test_manual_migration_command_requires_explicit_confirmation_and_database_url():
    migration_command = (BACKEND_DIR / "migrate.sh").read_text(encoding="utf-8")
    dockerfile = (BACKEND_DIR / "Dockerfile").read_text(encoding="utf-8")

    assert 'ALLOW_DATABASE_MIGRATION:-' in migration_command
    assert '!= "1"' in migration_command
    assert 'DATABASE_URL:-' in migration_command
    assert "python -m alembic upgrade head" in migration_command
    assert "COPY migrate.sh ." in dockerfile


class FakeConnection:
    def __init__(self, dialect: str):
        self.dialect = type("Dialect", (), {"name": dialect})()
        self.events: list[str] = []

    def exec_driver_sql(self, statement: str, parameters: tuple[int, int]) -> None:
        self.events.append(statement.split("(")[0].strip())
        assert parameters == (1162627393, 20261109)

    def commit(self) -> None:
        self.events.append("commit")


def test_postgresql_advisory_lock_commits_before_migrations_and_release():
    connection = FakeConnection("postgresql")

    assert acquire_migration_lock(connection)
    assert connection.events == ["SELECT pg_advisory_lock", "commit"]

    release_migration_lock(connection)

    assert connection.events == [
        "SELECT pg_advisory_lock",
        "commit",
        "SELECT pg_advisory_unlock",
        "commit",
    ]


def test_sqlite_migration_does_not_acquire_postgresql_advisory_lock():
    connection = FakeConnection("sqlite")

    assert not acquire_migration_lock(connection)
    assert connection.events == []
