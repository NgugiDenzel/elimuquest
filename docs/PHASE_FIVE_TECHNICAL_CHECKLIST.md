# Phase Five Technical Checklist

Audit date: 2026-10-29. No public deployment or active-database write was performed.

| Check | Command / method | Result and evidence |
|---|---|---|
| Backend automated tests | `cd backend; python -m pytest -q` | **27 passed**; one Starlette/httpx `TestClient` deprecation warning |
| Backend lint | `cd backend; python -m ruff check app tests scripts` | **Passed** |
| Frontend tests | `npm test -- --runInBand` | **6 passed** across 2 suites, including new AuthProvider tests |
| TypeScript | `npx tsc --noEmit` | **Passed** |
| Expo lint | `npx expo lint` | **0 errors, 27 warnings**; the prior `react-hooks/set-state-in-effect` AuthProvider error is resolved |
| Web bundle | `npx expo export --platform web` | **Passed**; web bundle exported to `dist` |
| Expo SDK package compatibility | `npx expo install --check` | Could not complete; registry connection returned `ECONNRESET` |
| Expo package versions | `package.json`, `npm ls --omit=dev --depth=3 expo expo-constants expo-router` | Expo is 58.0.17; direct `expo-constants` is 17.0.8 and direct Expo Router is 4.0.22. SDK compatibility remains unverified; native build not run. |
| Python dependency advisories | `python -m pip show pip-audit` | Tool not installed; no Python advisory report |
| Production npm advisories | `npm audit --omit=dev --json` | **19** reported: 5 high, 7 moderate, 7 low. Do not apply the proposed SDK-major downgrade automatically. |
| Backend health | `GET http://localhost:8000/health` | HTTP 200, `{"status":"ok"}` |
| Backend readiness | `GET http://localhost:8000/readiness` | HTTP 200, `{"status":"ready"}` |
| Web service | `GET http://localhost:8081/` and shared browser page | HTTP 200; browser showed `/welcome`. Authenticated lesson UI was not repeated in this audit. |
| Browser CORS | OPTIONS preflight from `http://localhost:8081` | HTTP 200; exact configured origin returned |
| Connection error regression | `npm test -- --runInBand` | Mocked connection refusal, HTTP 401, timeout, and malformed success body all retain distinct diagnostics |
| AuthProvider hook regression | `npx eslint src/providers/AuthProvider.tsx src/providers/AuthProvider.test.tsx`; Jest suite | **Passed**; restoration and failed-profile hydration covered |
| Scoring and publication APIs | Backend API tests | Correct/incorrect answers, short-answer normalization, duplicate answer rejection, incomplete completion rejection, idempotent completion, role boundaries, and blocked publication covered |
| Importer dry-run/idempotency | `python -m app.content.importer content-packages\coverage-expansion`; corresponding Mathematics and Grade 6 package commands | Expansion: 26 packages, 0 created, 58 unchanged. Mathematics: 36 packages, 0 created, 36 unchanged. Grade 6 package: 0 created, 5 unchanged. |
| Content audit export | `python backend\scripts\export_phase_five_audit.py` | Read-only database access; exported 125 lesson, 449 question, 77 topic-coverage, and 57 source rows |
| SQLite integrity / foreign keys | Python `sqlite3`: `PRAGMA integrity_check`, `PRAGMA foreign_key_check` | Active DB and backup integrity `ok`; zero FK violations |
| Isolated backup restore | SQLite backup API into a temporary separate file | Passed; integrity `ok`, zero FK violations, expected table counts; temporary copy removed |
| Docker Compose | `docker compose -f infra\docker-compose.yml config --quiet` | Not run; Docker CLI unavailable |
| Native builds / device checks | iOS, Android, physical-device runs | Not run; no native build or authenticated mobile device test was performed |
| Backend static type check | Repository configuration | No separate backend type-check command is configured |

## Configuration and behavior review

- `backend/elimuquest.db` is the active local database when Uvicorn is launched from the
  `backend` directory. `DATABASE_URL` can override it.
- The API uses the browser hostname or Expo host for development; physical phones require
  LAN reachability, a backend bind to `0.0.0.0`, and possibly an explicit
  `EXPO_PUBLIC_API_URL`. Production frontend builds do not fall back to localhost.
- CORS is origin-allowlisted and does not use a wildcard with credentials. Deployed web
  origins still need explicit HTTPS values.
- Production Docker configuration now sets `APP_ENV=production`; configuration validation
  rejects the development JWT secret, default SQLite URL, and local/non-HTTPS CORS origins.
- Local Postgres Compose no longer contains a shared password; it requires a unique
  `POSTGRES_PASSWORD` and binds its port to loopback.
- No production HTTPS endpoint, hosted database, monitoring, error tracking, backup
  scheduler, or deployment pipeline was verified.
- No secret values or learner-identifying data were included in generated audit artifacts.

## AuthProvider lint resolution

The lint rule was triggered because initial session restoration synchronously invoked
state updates from the effect call path. The effect now schedules restoration in a
microtask, leaving the storage/API work asynchronous and preserving loading, error,
retry, and token behavior. The AuthProvider has two focused tests: no-token hydration and
failed profile restoration with hydration completion. ESLint reports no remaining
AuthProvider error.

## Prior connectivity incident

The existing regression report records `POST /api/v1/auth/register` failing with
`ERR_CONNECTION_REFUSED` when no process was listening on port 8000. Starting Uvicorn
resolved that incident. In this audit the backend and web processes were reachable, so
the old outage was not reproduced as a current failure. The frontend now gives separate
diagnostics for transport failure, timeout, HTTP status, and invalid JSON.
