# ElimuQuest Staging Deployment Plan

**Status:** Planning only — no service, database, EAS project, or deployment was created.
**Assessment date:** 2026-10-29
**Target:** A staging-only web preview using EAS Hosting, Render FastAPI, and PostgreSQL.
**Release decision:** Do not invite real students or teachers until the blockers below are closed and the learner workflow is verified in staging.

## Executive assessment

| Area | Finding |
|---|---|
| Expo web deployment | Feasible without changing the app architecture. `npx expo export --platform web` has already succeeded and produced `dist/`. EAS Hosting supports Expo Router exports. |
| API base URL | Production web builds must receive `EXPO_PUBLIC_API_URL` at export time, set to the HTTPS Render API origin without `/api/v1`. It is public client configuration, not a secret. |
| PostgreSQL | Supported by SQLAlchemy models and the installed `psycopg` 3 driver. Use a Render internal connection URL with the SQLAlchemy driver prefix `postgresql+psycopg://`. |
| Schema | Three Alembic revisions exist. `alembic upgrade head` creates/upgrades schema; it does not seed curriculum or migrate the local SQLite database. |
| Fresh-database bootstrap | Not beta-ready. `app.seed` is development-only and inserts demo content. The importer adds content to already-created catalog records; there is no approved production bootstrap for a clean database or initial admin. Do not set `APP_ENV=development` in a hosted service to work around this. |
| Health | Use `/readiness` for the Render health-check path because it verifies a database query. `/health` only verifies that the API process responds. |
| Real-learner release | Not ready. Phase Five and Phase Six reports retain content-review, licensing, child-data/privacy, security, and operations blockers. |

## Repository findings

- The Expo app uses SDK 58.0.21, Expo Router 58.0.28, React Native 0.88.1, and TypeScript. `app.json` does not set `web.output`; the currently successful export produced a single `dist/index.html` plus static assets. EAS Hosting supports this SPA output. Confirm direct routes and browser refresh on the staging URL before beta.
- There is no `eas.json` or existing EAS project link. EAS project linking and choosing a preview subdomain are one-time setup steps; this plan does not perform them. EAS preview URLs are publicly reachable by URL; an alias is not access control.
- `backend/pyproject.toml` requires Python 3.12 or later and includes FastAPI, Uvicorn, SQLAlchemy, Alembic, and `psycopg[binary]`.
- The existing `backend/Dockerfile` uses Python 3.12 but hardcodes port 8000 and starts Uvicorn without applying migrations. Use Render's Docker runtime with a dashboard Docker Command override below; do not deploy the existing image command unchanged.
- The SQLAlchemy engine only adds SQLite-specific connection arguments for SQLite; `Uuid`, `JSON`, and the declared models are SQLAlchemy types. Alembic reads the same `DATABASE_URL`. The PostgreSQL URL must use the installed psycopg 3 dialect.
- Migrations are:
  1. `b60788453753_initial_learning_platform_schema.py`
  2. `9610475c2ba8_add_curriculum_metadata_and_review_.py`
  3. `6f819c73f5d4_track_ai_assisted_curriculum_drafts.py`
- There is no SQLite-to-PostgreSQL data migration in this repository. Do not point staging at `backend/elimuquest.db`, copy that file to Render, or migrate its learners.
- Registration is public and always creates a student role. There is no teacher onboarding flow, in-app account deletion, or safe production admin bootstrap. Admin role changes currently require trusted out-of-band operator access.

## Services and dashboard configuration

Create these only after reviewing the release blockers and deciding to proceed with an isolated staging environment. Use a dedicated staging database; do not connect to or overwrite the local SQLite database.

### 1. Render PostgreSQL

1. In the Render Dashboard, create a **PostgreSQL** database for staging.
2. Select a region and use the same region for the API service.
3. For any test involving real people, choose a paid plan with backups and retention appropriate to the approved policy. Do not use the free database for learner data; its current documented lifetime/backup limitations are listed under [Cost and plan constraints](#cost-and-plan-constraints).
4. Keep the database private. Do not expose a public database port.
5. Copy the **internal** connection URL from Render. Configure the web service's `DATABASE_URL` using that URL, replacing only the driver prefix with `postgresql+psycopg://` if the provided URL starts with `postgresql://`. Preserve its generated credentials and URL encoding; do not paste it into source control, EAS, or a client variable.
6. Confirm the application service can reach the database using Render's internal network.

### 2. Render FastAPI web service

1. Create a **Web Service** linked to the ElimuQuest repository and the intended staging branch.
2. Set **Root Directory** to `backend`.
3. Choose the **Docker** runtime. Set **Dockerfile Path** to `Dockerfile` and **Docker Context Directory** to `.` relative to the configured root directory. The Dockerfile installs `pyproject.toml` dependencies and copies the app and Alembic files from this directory.
4. Override the Docker command in the service's **Docker Command** field with:

   ```sh
   /bin/sh -c 'alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"'
   ```

   This replaces the Dockerfile's hardcoded-port `CMD`, runs schema migrations, then binds Uvicorn to Render's assigned port. Keep this first staging service at one instance; do not run simultaneous startup migrations on multiple replicas. For a scaled service, move migrations to a serialized release/pre-deploy step supported by the selected Render plan before scaling.
5. Set the health-check path to:

   ```text
   /readiness
   ```

   `/health` is useful for a process-only check, but it does not establish database readiness.
6. Set only these backend environment variables:

   | Variable | Value / handling |
   |---|---|
   | `APP_ENV` | `production` |
   | `DATABASE_URL` | Render internal PostgreSQL URL using `postgresql+psycopg://`; secret |
   | `JWT_SECRET` | Generate a unique random secret of at least 32 characters with a secure password manager/generator and enter it directly in Render as a secret; never reuse a local or other environment's value |
   | `JWT_ISSUER` | `elimuquest-api` (matches the current application default; keep stable for this environment) |
   | `ACCESS_TOKEN_MINUTES` | `60` (current default; adjust only with an approved session policy) |
   | `CORS_ORIGINS` | Exact HTTPS EAS staging alias origin, e.g. `https://<chosen-preview-subdomain>--staging.expo.app`; no path, trailing slash, wildcard, or unrelated origin |
   | `LOG_LEVEL` | `INFO` |

   Render supplies `PORT`; do not hardcode it or expose it as a static value. Do not put `DATABASE_URL` or `JWT_SECRET` in the frontend.
7. Deploy only the staging branch. Verify the deployment logs do not contain secret values, and check `https://<render-service>.onrender.com/health` and `/readiness`.

### 3. EAS Hosting web preview

1. Sign in to the Expo account and create/link the EAS project for this app. `npx eas-cli@latest init` links the repository project and can update `app.json` with an EAS project ID; review that diff before committing it.
2. In the EAS project dashboard, enable Hosting and choose a unique preview subdomain. It is reserved to the project; choose it deliberately.
3. In the EAS **preview** environment, add:

   | Variable | Value / handling |
   |---|---|
   | `EXPO_PUBLIC_API_URL` | `https://<render-service>.onrender.com` |

   This value is compiled into the web bundle and is visible to users. It must not contain credentials or secrets. Do not include `/api/v1`; the client appends that path.
4. Add the exact stable staging alias origin to Render's `CORS_ORIGINS`, save the backend setting, and redeploy/restart the API if required.
5. From the repository root, authenticate the local EAS CLI, pull the EAS preview environment for the export, and export/deploy:

   ```powershell
   npx eas-cli@latest login
   npx eas-cli@latest env:pull --environment preview
   npx expo export --platform web
   npx eas-cli@latest deploy --alias staging
   ```

   Run the export from the same environment where the preview variable was pulled. Check the generated output for the expected HTTPS API origin without printing or publishing unrelated environment values. EAS deployments are immutable; the `staging` alias points to the current preview deployment.
6. Set Render `CORS_ORIGINS` to the precise alias origin shown by EAS, with scheme and host only. If testing the unique deployment URL instead of the alias, add that exact origin temporarily and remove it afterward.
7. Do not run `eas deploy --prod`, `eas deploy:alias --prod`, or assign the production alias as part of staging.

EAS Hosting serves the **web** build only. Its preview URL is publicly reachable by anyone who has the link; the `staging` alias does not add a password or access list. Do not treat it as private or share it with learners until access and account-creation controls are approved. iOS/Android releases require separate EAS Build setup, mobile API configuration, device testing, and review; no native app is deployed by this plan.

## Environment-variable inventory

| Environment | Variable | Public? | Purpose |
|---|---|---:|---|
| Render API | `APP_ENV` | No | Enables production settings validation |
| Render API | `DATABASE_URL` | **No — secret** | Private PostgreSQL connection |
| Render API | `JWT_SECRET` | **No — secret** | Signs access tokens |
| Render API | `JWT_ISSUER` | No | JWT issuer validation |
| Render API | `ACCESS_TOKEN_MINUTES` | No | Access-token expiry |
| Render API | `CORS_ORIGINS` | No | Exact allowed browser origins |
| Render API | `LOG_LEVEL` | No | Server logging level |
| Render platform | `PORT` | No | Assigned listener port; supplied by Render |
| EAS preview/web bundle | `EXPO_PUBLIC_API_URL` | **Yes** | HTTPS API origin embedded at export time |

No values for secrets are included in this file. `EXPO_PUBLIC_*` values are not secret even if stored in a dashboard environment.

## Database migration and initial content

### Schema

After configuring a **new, empty staging PostgreSQL database**, Render's start command runs:

```sh
alembic upgrade head
```

This is a schema migration, not a data import. First verify the database identity and backup/recovery plan. Do not use the app's local SQLite URL or execute a destructive reset command.

### Catalog and content

The current deployment cannot yet be made into a populated learner beta by migrations alone:

- `python -m app.seed` explicitly refuses to run unless `APP_ENV=development`; it inserts demo catalog/content and is not an approved production initialization mechanism.
- The content importer expects the target subject/topic catalog to exist, imports drafts, and does not approve or publish them.
- The repository has no production-safe catalog bootstrap, initial admin creation, or real-data migration command.

Before any learner beta, create and review an idempotent, audited staging bootstrap path for approved catalog/content that does **not** create demo users, publish unreviewed content, or run with development security settings. Create an initial administrator through a separately audited, secret-safe operator procedure; do not change public registration to accept a role. Until those processes exist, staging can test API liveness/readiness and account flows, but it cannot prove the intended curriculum learner journey against a fresh database.

Do not migrate the active SQLite database or real learner records under this plan. If a future, separately approved migration is needed, it requires its own mapping, dry-run, row-count/integrity checks, backup, access-control plan, and rollback rehearsal.

## Verification checklist

Use synthetic accounts and content only. Record deployment IDs, timestamps, HTTP status codes, and test outcomes without recording passwords, tokens, or student data.

1. **Service and database**
   - `GET /health` returns HTTP 200 and `{"status":"ok"}`.
   - `GET /readiness` returns HTTP 200 and `{"status":"ready"}` after connecting to PostgreSQL.
   - Stop/restart or redeploy the staging service and confirm PostgreSQL data persists.
   - Confirm Render logs have no connection string, JWT secret, passwords, or bearer tokens.
2. **TLS and CORS**
   - Open the EAS staging alias in a browser and confirm API calls use `https://<render-service>.onrender.com`.
   - Confirm preflight and API requests from the exact EAS alias succeed.
   - Confirm an unlisted browser origin is not allowed. CORS is not an authorization control.
3. **Authentication and API**
   - Register a synthetic staging account; log in; call authenticated `/api/v1/me`.
   - Verify unauthenticated learner routes remain unauthorized and a student cannot access admin endpoints.
   - Verify invalid credentials and server/network failures are surfaced distinctly; never display server traces or secrets.
4. **Curriculum and learner journey**
   - Only after the approved catalog/content bootstrap and reviewer setup are available, verify representative Grade 6, Grade 9, and legacy Form 4 records as separate curricula where supported.
   - Confirm published lessons are returned for the matching learner level, a lesson opens, questions load, answers are graded, and completion/progress are persisted.
   - Confirm a learner cannot access a lesson assigned to another curriculum/level.
   - Test direct navigation and browser refresh on lesson routes, not only navigation from the home screen.
5. **Application checks before each staging export**

   From the repository root:

   ```powershell
   npx tsc --noEmit
   npx expo lint
   npx expo export --platform web
   ```

   From `backend`:

   ```powershell
   python -m pytest -q
   python -m ruff check app tests
   ```

   These local checks do not replace the hosted HTTPS/CORS/database/auth/learner-journey checks above. Native iOS and Android builds were not part of this web-only plan.

## Phase Five/Six blockers before real-student beta

The existing release reports say **NOT READY**. Resolve and document closure evidence before giving real students or teachers access:

1. **Content accuracy and independent review:** Phase Five documented 124 published lessons, including missing objectives/explanations/feedback/source locators; Phase Six did not complete expert review of the full catalog. Current content must be reviewed and corrected in scope.
2. **Source rights:** the reports identify restricted and unverified source entries. Obtain applicable rights or remove/rework unapproved material before external use. Do not describe content as officially KICD-approved without evidence.
3. **Child-data safeguards:** obtain specialist review and implement the required privacy/consent/guardian, retention, deletion, support, and leaderboard decisions. The inspected app has no privacy notice, consent workflow, or account-deletion flow.
4. **Internet-facing account security and beta access:** public registration/login have no rate limiting, and the EAS preview URL itself is not access-controlled. Add and test rate limiting and an approved invite/access process before exposure. Registration currently grants only student access; teacher onboarding and safe initial admin provisioning are unresolved.
5. **Production operations:** establish monitoring/error reporting, backup schedule and tested restore, service ownership, incident response, access controls, and an approved rollback procedure. Free Render database does not provide suitable real-learner backup protection.
6. **Dependencies and platform coverage:** Phase Six reports three high npm audit advisories and no physical-device/native build validation. Triage advisories safely and complete the release's required web/native checks.
7. **Fresh database and content:** develop and test the production-safe bootstrap/import/review flow described above.

These are release gates, not claims that a particular law has been violated. Passing software tests alone is not evidence of curriculum quality, copyright clearance, privacy compliance, or beta readiness.

## Cost and plan constraints

Pricing and included amounts can change; figures below reflect provider documentation reviewed on **2026-10-29**. Confirm the selected plan, region, storage, backup, bandwidth, and tax in the provider dashboards before creating resources.

- **Expo EAS Hosting:** the documented Free tier includes a limited allowance (100,000 requests/month, 1,000,000 CPU-ms, and 1 GB storage); overages/limits and preview retention apply. Expo lists a paid Starter plan at **$19/month** for additional allowances/custom-domain options. See [Expo pricing](https://expo.dev/pricing#host) for current terms. A project may begin at $0 for a small preview if it remains within the current free allowance.
- **Render:** Free web services and PostgreSQL are listed at $0 for testing. A free web service spins down after 15 minutes without inbound traffic and can take about a minute to start again. Free PostgreSQL expires 30 days after creation, has a 14-day upgrade grace period before deletion, and does not provide backups. Render explicitly says free instances are not for production. See [Render Free instances](https://render.com/docs/free).
- **Real learner data:** the plan is not safely $0. Budget for an always-on API service plus paid PostgreSQL with backups and adequate retention. Render prices depend on selected compute/database/storage and billing; consult the live [Render pricing page](https://render.com/pricing) and dashboard quote. No exact paid Render total is asserted here because it was not independently verifiable from the published pricing text in this assessment.

The closest-to-zero option is a non-sensitive, synthetic-data technical preview on free resources, with cold-start/expiry/backup limitations accepted and no learner invites. A real-student beta should use persistent paid PostgreSQL and an operationally suitable API plan.

## Rollback and recovery

1. **Web:** every EAS deployment is immutable. Keep the last verified deployment ID. If staging UI fails, reassign the `staging` alias to that deployment with:

   ```powershell
   npx eas-cli@latest deploy:alias --id=<known-good-deployment-id>
   ```

   Do not promote it to production.
2. **API:** use Render's deployment history to redeploy the last known-good staging commit. Keep the service at one instance during initial staging.
3. **Database:** capture a supported backup/restore point before any migration against a database containing data; rehearse restore into a separate database. Do not assume a code rollback can reverse a schema change. Prefer a forward fix or restore the verified database backup only under the approved recovery procedure.
4. **Data safety:** the proposed first staging database should contain only synthetic records, making it disposable only after confirming that no real data was entered. Never overwrite or delete `backend/elimuquest.db` as a rollback step.
5. **Secrets:** rotate the staging JWT secret if it is exposed; users will need to reauthenticate because existing tokens will no longer validate.

## Exact next dashboard actions

Nothing has been deployed or created. After resolving the beta gates, the next safe order is:

1. Review the Phase Five/Six release blockers with the responsible education, privacy, and operations owners; decide whether this is a synthetic technical preview or an approved real-learner beta. Treat the EAS URL as public, not a private dashboard preview.
2. For a synthetic preview, create a **staging-only** Render PostgreSQL database and one Render web service in the same region, set the commands/environment above, and check `/readiness`. Do not add learner data.
3. Link the app to the Expo project, select a staging-only preview subdomain, set `EXPO_PUBLIC_API_URL` in the EAS **preview** environment, export and deploy with the `staging` alias, then verify HTTPS, CORS, routes, and the database/API checks.
4. Before inviting anyone, complete the safe catalog/content/admin bootstrap, all release-gate work, backup/restore rehearsal, and the full synthetic learner journey. Use a paid persistent database/service suitable for the approved beta; do not promote the EAS production alias.

## Provider documentation

- [Expo SDK 58 documentation](https://docs.expo.dev/versions/v58.0.0/)
- [EAS Hosting: get started](https://docs.expo.dev/eas/hosting/get-started/)
- [EAS Hosting: deployments and aliases](https://docs.expo.dev/eas/hosting/deployments-and-aliases/)
- [EAS environment variables](https://docs.expo.dev/eas/environment-variables/)
- [EAS pricing](https://expo.dev/pricing#host)
- [Render free instances](https://render.com/docs/free)
- [Render Docker services](https://render.com/docs/docker)
- [Render health checks](https://render.com/docs/health-checks)
- [Render monorepo support](https://render.com/docs/monorepo-support)
- [Render PostgreSQL](https://render.com/docs/postgresql-creating-connecting)
- [Render pricing](https://render.com/pricing)
