# ElimuQuest API

FastAPI modular-monolith API. PostgreSQL is the deployment database; SQLite is supported for a local smoke test and automated tests.

## Local setup (PowerShell)

```powershell
cd C:\Users\Admin\Desktop\elimuquest\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The repo includes a local SQLite database. Do not copy a fresh-database `.env`, migrate, or seed over an existing working database as part of routine startup. To initialize a brand-new database only, copy `.env.example` to `.env`, then run `alembic upgrade head` and `python -m app.seed` once before starting the server.

For browser development on this computer, the command above binds the backend to loopback. For testing on a physical phone, bind to all interfaces so the phone can reach the computer:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000/docs` or check `/health` and `/readiness`. Keep the backend process running while using the app. Do not run `python -m app.seed` against an existing database unless intentionally creating a new development database.

For local PostgreSQL, install Docker Desktop, set a unique `POSTGRES_PASSWORD` in the ignored project-root `.env`, and run `docker compose --env-file ..\.env -f ..\infra\docker-compose.yml up -d postgres`. The container port is bound to loopback only. Set `DATABASE_URL=postgresql+psycopg://elimuquest:<URL-encoded-password>@localhost:5432/elimuquest` in `backend/.env` before running migrations. Do not reuse the development password in a deployed environment. The Docker image defaults to `APP_ENV=production` and refuses to start with the development JWT secret or default SQLite URL; provide a unique `JWT_SECRET` and explicitly configured persistent `DATABASE_URL` and production HTTPS `CORS_ORIGINS`. Docker is not installed in the current implementation environment.

## Tests and lint

```powershell
pytest -q
ruff check app tests
```

The tests use an isolated in-memory SQLite database. They do not connect to or modify a hosted database.

## Client configuration

In the repository root, configure `EXPO_PUBLIC_API_URL` when the default is unsuitable. In development, web uses the hostname serving the app with port 8000; Expo native development uses the Expo development host with port 8000. This supports local browsers, simulators and LAN-connected phones, but phones still require the backend to bind to `0.0.0.0`, the computer's LAN address to be reachable, and port 8000 to be allowed through the local firewall. Set `EXPO_PUBLIC_API_URL=http://<computer-LAN-IP>:8000` in the root environment when automatic host detection is unsuitable, then restart Expo so the value is included in its bundle.

The backend's `CORS_ORIGINS` must contain the exact browser origin, including scheme and port (for example `http://localhost:8081` or `http://192.168.1.20:8081`). Native apps do not use browser CORS. Do not use wildcard origins with credentials. Never put backend secrets in an `EXPO_PUBLIC_` variable. Production builds must set `EXPO_PUBLIC_API_URL` to the real HTTPS API origin before building; they do not fall back to a localhost development URL.

Backend settings are in `backend/.env.example`. Replace `JWT_SECRET` with a random secret of at least 32 characters in every deployed environment. Never use the development default in production. Set CORS to the exact web origins in deployment.

## Curriculum and content packages

The seed creates curriculum subject offerings for CBC/CBE Grade 6, CBC/CBE Grade 9 and 8-4-4 Form 4. The legacy fictional examples remain unassigned to those levels. The authorized Grade 6 Whole Numbers book excerpt is supplied as a separate JSON package and imported as draft content; it is not auto-published.

Review the JSON package contract and run a read-only validation before importing:

```powershell
python -m app.content.importer .\content-packages\example-grade-9.json
```

The example deliberately fails provenance validation because its citations are placeholders. To import an actual package as a draft, cite the source PDF page/section and pass `--apply`. Admins can review status changes at `/api/v1/admin/lessons` and `PATCH /api/v1/admin/lessons/{lesson_id}/status`; there is no in-app authoring editor.

The Grade 6 Whole Numbers excerpt package can be validated and imported with:

```powershell
python -m app.content.importer .\content-packages\grade6-whole-numbers-pupils-book.json
python -m app.content.importer .\content-packages\grade6-whole-numbers-pupils-book.json --apply
```

The supplied six-page excerpt references an answer key that is not included in the file. Quiz answer keys are calculated independently and must be reviewed; this limitation is shown in the lesson source reference and admin review screen. The import does not approve or publish lessons.

## Behavior and limitations

- Public registration always creates a student account. Administrator role changes require trusted out-of-band database/operator access; a registration payload cannot set roles.
- Passwords use Argon2id hashes. Access tokens are signed HS256 JWTs with issuer and expiry claims.
- Only published lessons are available to students. Correct answers are not included in lesson responses.
- Each session permits one submitted answer per question. A completion is accepted once all answers exist. A completed lesson gets `10 + 5 × correct answers` XP; its score is the correct-answer percentage. Duplicate completion returns the recorded result without another XP award.
- Streak and daily goal activity counts completed lessons, using each student's IANA timezone (default `Africa/Nairobi`). The current streak accepts activity today or yesterday.
- Demo content is fictional and is not verified KICD content or official exam material.
- No notification, dedicated practice-session, admin content authoring UI, review-scheduling engine, or account-deletion flow exists in the frontend. These require additional product work. No external identity provider or production deployment is configured.
- Implement rate limiting at the edge/API gateway before exposing public registration to the internet. Review student privacy, retention, account deletion, CORS, TLS, backups, and child-data obligations before production; this code is not a legal-compliance claim.
