# Verification baseline

Checked on 2026-10-24 during curriculum expansion.

| Check | Result | Notes |
| --- | --- | --- |
| Frontend TypeScript | Passed | `npm run typecheck` uses a larger Node stack because the default stack overflows in this project’s TypeScript 6 dependency graph. |
| Expo web export | Passed | `npx expo export --platform web --output-dir dist`, including curriculum selector, content pages, and admin review screen. |
| Browser frontend/API flow | Passed | Registered a student, loaded dashboard and lesson, submitted answers, completed the lesson, and verified persisted progress after reload. |
| Python | Available | Python 3.14.8 is installed; backend declares Python 3.12+. |
| Docker / PostgreSQL CLI | Blocked | Neither `docker` nor `psql` is installed; PostgreSQL cannot be run locally in this environment. |
| Backend dependencies | Installed | `python -m pip install -e '.[dev]'` completed successfully. |
| Backend tests | Passed | `python -m pytest -q`: 9 passed, including level/subject isolation, student/admin review permissions, import dry-run/idempotency, published-content protection, and existing auth/reward behavior. |
| Backend lint | Passed | `python -m ruff check app tests alembic`. |
| Migration consistency | Passed | Additive migrations applied to local SQLite; `python -m alembic check` reports no schema drift. |
| PostgreSQL | Not verified | Docker and `psql` are unavailable; SQLite is used locally and in tests. |

## Current external blockers

- No Docker CLI, local PostgreSQL server, or PostgreSQL CLI. Use SQLite for local/test execution; the backend remains configured for PostgreSQL when a database URL is supplied.
- No production API host, production database, or authentication provider credentials are configured.
