# ElimuQuest backend release candidate

**Status: BACKEND RELEASE DEPLOYED.** The reviewed 23-file backend allowlist was
committed as `bef66e7` and pushed to `main`. Render deployed the existing API
service and the live Mathematics endpoints were verified. The user selected a
backend-only release; the frontend and its sign-in flow remain unchanged.

## Release allowlist

Only the following files and change hunks belong in this candidate:

### API and runtime

- `backend/app/api/v1/mathematics.py` — the dedicated router with the ten
  Mathematics paths.
- `backend/app/main.py` — only the Mathematics router import and registration;
  exclude the unrelated lesson-review changes in the dirty file.
- `backend/app/api/dependencies.py` — optional learner authentication; malformed
  supplied bearer tokens remain unauthorized, and administrator checks remain
  mandatory for review endpoints.
- `backend/app/models/mathematics.py` and
  `backend/app/schemas/mathematics.py` — isolated persistence models and request
  and response schemas, without changing shared entity/schema files.
- `backend/app/services/mathematics.py` and
  `backend/app/services/mathematics_coverage.py` — curriculum, lesson, answer,
  coverage, and review-pack logic.
- The five JSON inputs in `backend/content-packages/` named in the Dockerfile.
  They are runtime assets, not database publication data.
- Those inputs are `mathematics-learning-pack.json`,
  `mathematics-learning-sequences.json`,
  `mathematics-number-systems-phase-b.json`,
  `mathematics-number-systems-assessment-phase-b.json`, and
  `mathematics-curriculum-register.json`.
- `backend/Dockerfile` — copies the five assets and migration files and runs as
  UID/GID `10001`.
- `backend/start.sh` — runs `alembic upgrade head` before starting Uvicorn and
  uses Render's `PORT`.
- `backend/migrate.sh` — separately guarded manual migration command, copied into
  the image.
- `backend/pyproject.toml` — adds `python-dotenv`, needed by the backend's
  settings configuration.
- `backend/alembic.ini`, `backend/alembic/env.py`, and
  `backend/app/db/migration_lock.py` — explicit database URL handling and a
  PostgreSQL advisory lock around startup migrations.

### Database migrations

- `backend/alembic/versions/72a31e5f4c10_add_content_provenance_and_audit.py`
- `backend/alembic/versions/2c8a47f1d963_add_mathematics_review_and_feedback.py`

The candidate must **exclude**
`backend/alembic/versions/5f1a9c8d2e40_add_auth_rate_limits_and_admin_bootstrap_audit.py`.
That later migration is unrelated to Mathematics. With only the two listed
revisions included, the candidate's Alembic head is `2c8a47f1d963`.

### Tests and release record

- `backend/tests/test_mathematics_router.py` — Mathematics routes, access control,
  content behavior, and error cases.
- `backend/tests/test_deployment_migration.py` — startup migration ordering,
  guarded manual migration, and advisory-lock behavior.
- `RELEASE_CANDIDATE_MANIFEST.md` — this allowlist and release checklist.

Do not stage entire dirty files just because they appear above: the commit included
only the Mathematics registration hunk from `main.py`. All unrelated worktree
changes were left unstaged and uncommitted. No content publication was performed.

## Excluded from this release

- All frontend/UI changes, including Mathematics screens, guest-first onboarding,
  API-client changes, and route/navigation changes. The selected scope keeps the
  live frontend and existing sign-in flow unchanged.
- Broader local Mathematics content-development tests and draft assets, including
  `backend/tests/test_mathematics.py`; these are outside the runtime API package
  and remain unstaged.
- The shared `backend/app/api/v1/router.py`, broad model/schema edits, and unrelated
  authentication, admin, resource, lesson, learner-session, curriculum, or content
  functionality.
- Revision `5f1a9c8d2e40` and its auth rate-limit/admin-bootstrap dependencies.
- Local content publication/export scripts and all unrelated subject/content work.
- Cloudflare Pages setup. The existing Render static site is the frontend host; no
  replacement service or duplicate frontend is needed.

All other worktree changes must remain unstaged and unmodified by this release.

## Route and dependency status

The local OpenAPI document registers ten Mathematics paths. Their route definitions
are isolated in `mathematics.py`; public curriculum, lesson, validation, and answer
operations use bundled JSON. Coverage and educator-review endpoints use the
database. Feedback accepts anonymous submissions, but validates any supplied token.
Review decisions and the feedback inbox require administrator authorization. No
authentication bypass or synthetic success response is part of this candidate.

The exact paths are:

- `/api/v1/mathematics/curriculum`
- `/api/v1/mathematics/coverage`
- `/api/v1/mathematics/coverage/validation`
- `/api/v1/mathematics/coverage/questions/quality`
- `/api/v1/mathematics/lessons/{lesson_id}`
- `/api/v1/mathematics/lessons/{lesson_id}/answers`
- `/api/v1/mathematics/feedback`
- `/api/v1/admin/mathematics/number-systems/review`
- `/api/v1/admin/mathematics/number-systems/review-decisions`
- `/api/v1/admin/mathematics/number-systems/feedback`

The API is not independent of shared infrastructure: it uses the existing database
session, `User` model, JWT dependencies, settings, and FastAPI app. The standalone
Mathematics models/schemas avoid shipping the unrelated dirty shared model/schema
changes. The migration chain is a required shared database dependency.

The five bundled JSON files were validated previously: they parse, produce 31
lessons and 257 questions, and preserve the 193 topic-linked and 64 intentionally
unlinked questions. No educational content is changed by this release.

## Migration assessment

The required migration order is linear:

```text
a4c73e6b91d2 (reported production revision)
  -> 72a31e5f4c10 (content provenance fields and audit table)
  -> 2c8a47f1d963 (Mathematics review and learner-feedback tables)
```

Revision `72a31e5f4c10` adds non-null lesson provenance fields with server defaults,
check constraints, and an audit table with foreign keys and indexes. Revision
`2c8a47f1d963` adds review-decision and learner-feedback tables, constraints,
foreign keys, and indexes. Neither migration transforms or deletes existing user,
authentication, or learner-activity rows. The migration chain reached `2c8a47f1d963`
in a rehearsal on a disposable local PostgreSQL 18 database with synthetic records;
this was not a rehearsal on a Neon branch.

The Docker startup script runs `alembic upgrade head` before Uvicorn. With the
release allowlist, the Render deployment applied both migrations to production
before the new API started. The existing snapshot from 2026-11-09 has not been
restore-tested. Do not run content publication or downgrade migrations as rollback.

A fresh Neon child branch, `pre-mathematics-release-2026-11-10`
(`br-small-bread-b56supvf`), was created from the production branch on 2026-11-10
with data and schema through the current point in time and auto-delete set to Never.
The branch's `alembic_version` table was checked in the Neon console and contains
`a4c73e6b91d2` before deployment. After deployment, the production branch's
`alembic_version` was verified in the Neon console at `2c8a47f1d963`; the two
three expected tables (`content_audit_events`, `mathematics_review_decisions`, and
`learner_content_feedback`) are present. The backup branch remains at the pre-release
revision. This is a separate copy-on-write recovery point, not a Neon restore test
or migration rehearsal. Do not apply release migrations to this backup branch; use
a separate disposable child for any future Neon rehearsal.

## Existing Render configuration

The intended target is the existing Web Service `elimuquest-api`
(`srv-dbhr03afngtc73cc8gtg`) in project `My project`, Production environment:

- Repository `NgugiDenzel/elimuquest`, branch `main`.
- Root directory/build context `backend`; Dockerfile `Dockerfile`.
- Docker image command `sh start.sh`; health check `/readiness`.
- Auto-deploy is On Commit; PR previews are Off.
- Public API: `https://elimuquest-api.onrender.com`.
- Render supplies `PORT`. Existing environment keys include `APP_ENV`,
  `DATABASE_URL`, `JWT_SECRET`, `JWT_ISSUER`, `CORS_ORIGINS`,
  `ACCESS_TOKEN_MINUTES`, and `LOG_LEVEL`. Do not expose or copy secret values.

No new frontend environment variable is required for this backend-only candidate.
The existing Render frontend remains unchanged. Cloudflare Pages is not a release
blocker while that frontend remains the selected production host.

The Render deployment for commit `bef66e7` succeeded in 1m 1s. Its logs show both
migrations running in order and the Uvicorn server starting. Live verification
returned HTTP 200 for `/health`, `/readiness`, Mathematics curriculum, and a
Mathematics lesson. OpenAPI exposes all ten expected paths. The unauthenticated
administrator review route returns HTTP 401. No authenticated write route or
content-publication operation was invoked against production.

## Validation and remaining release gates

- Backend full suite: 127 passed, 2 skipped. The worktree also contains broader
  uncommitted content-development tests not in this allowlist.
- Focused Mathematics router tests: 8 passed; startup/migration tests passed.
- Frontend tests: 32 passed across 9 suites; TypeScript, Expo lint, and Expo web
  export passed. The frontend is excluded from this backend-only diff.
- The generated local web export contained no `DATABASE_URL`, `JWT_SECRET`, or
  `postgresql+psycopg://` matches; the export is not part of the release.
- Docker and Podman are unavailable locally; WSL 2 has no installed Linux
  distribution. Render successfully built and deployed the Docker image, which
  validates the production build and startup path; no separate local container
  smoke test was run.
- Ruff passed on the release-specific Python files. The 15 known findings in the
  unrelated resource registry and its test remain excluded.
- `git diff --check` and the staged release diff check pass.
- The live Render API returns 200 from `/health` and `/readiness`; OpenAPI exposes
  ten Mathematics paths.
- Production migrations through `2c8a47f1d963` occurred during the approved Render
  deployment. No content publication occurred.

### Completed release sequence

1. Reviewed and committed only the backend allowlist, leaving unrelated worktree
   changes untouched.
2. Created the never-auto-delete Neon pre-release branch and verified its starting
   revision was `a4c73e6b91d2`.
3. Pushed commit `bef66e7` to `main`; the existing Render API auto-deployed it.
4. Verified both production migrations completed, the Neon production revision is
   `2c8a47f1d963`, and all ten live Mathematics paths respond as expected.
5. Keep the frontend unchanged in this release. Consider Mathematics UI and any
   frontend changes as a separate, reviewed release.
