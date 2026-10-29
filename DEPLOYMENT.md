# ElimuQuest deployment handover

**Status (2026-10-29):** Neon Free project `elimuquest-beta` is in AWS US East 2 (Ohio), and Render Free service `elimuquest-api` is live in Ohio at `https://elimuquest-api.onrender.com`. `/health` and `/readiness` returned HTTP 200; all three Alembic revisions applied; synthetic registration/login, protected access, anonymous 401 behavior, CORS preflight, and login persistence after a service restart were verified. The database contains only the synthetic smoke account created for these checks; no real learner data was migrated or entered. No frontend has been deployed: the Cloudflare dashboard's Pages creation route fails to load its module scripts, and GitHub Pages is unavailable for this private repository on the current plan.
**Target:** A synthetic-data technical preview using Cloudflare Pages, Render Free, and Neon Free.
**Do not invite real learners:** The existing Phase Six beta gate is not ready for real student data.

## What is already configured

- The Expo web build is `npx expo export --platform web`; the output directory is `dist`.
- `app.config.js` uses a single-page web export. Leave `EXPO_BASE_PATH` unset on Cloudflare Pages; the Pages site is served from the domain root.
- The frontend reads `EXPO_PUBLIC_API_URL` at build time. Set it to the HTTPS API origin only, without `/api/v1` or a trailing slash. It is public client configuration, not a secret.
- The FastAPI entry point is `app.main:app` and its readiness endpoint is `/readiness`.
- `backend/pyproject.toml` includes FastAPI, Uvicorn, SQLAlchemy, Alembic, and psycopg 3. The models and migrations use SQLAlchemy types supported by PostgreSQL.
- `backend/Dockerfile` uses `backend/start.sh` to apply Alembic migrations and then bind Uvicorn to Render's `PORT` (with local fallback `8000`).
- The database is configured with `DATABASE_URL`; production settings reject the default local SQLite URL and the development JWT secret.

## Configure the services

Use the same region for Render and the Neon project where practical. Do not copy the repository's SQLite database to a hosted service.

### 1. Neon database

1. The `elimuquest-beta` project was created on the **Free** plan in AWS US East 2 (Ohio). Its default `production` branch is the target for this synthetic-data preview.
2. Keep the database private to the application connection. Copy its connection string from the Neon dashboard only into Render's secret `DATABASE_URL`; do not put it in Git, a frontend variable, or chat.
3. Configure Render's `DATABASE_URL` with that connection string using the SQLAlchemy psycopg driver prefix:

   ```text
   postgresql+psycopg://...
   ```

   Preserve the generated hostname, database, URL-encoded credentials, and TLS query parameters from Neon. Do not use a local SQLite path.

### 2. Create the Render API

1. In [Render](https://dashboard.render.com/), use the existing `elimuquest-api` Web Service from `NgugiDenzel/elimuquest`; do not create a duplicate service.
2. Set **Root Directory** to `backend`, runtime to **Docker**, and Dockerfile path to `Dockerfile`. The service is on the **Free** plan; keep it limited to this synthetic-data preview.
3. Leave **Docker Command** blank so Render uses the Dockerfile's `CMD ["sh", "start.sh"]`. Keep the service to one instance while migrations are run at startup.
4. Set the health-check path to `/readiness`.
5. Add these environment variables in Render's service settings:

   | Name | Value |
   |---|---|
   | `APP_ENV` | `production` |
   | `DATABASE_URL` | Neon connection URL with the `postgresql+psycopg://` driver prefix; secret |
   | `JWT_SECRET` | Unique random value, at least 32 characters; secret |
   | `JWT_ISSUER` | `elimuquest-api` |
   | `ACCESS_TOKEN_MINUTES` | `60` |
   | `CORS_ORIGINS` | The exact Cloudflare Pages origin, e.g. `https://<project>.pages.dev` |
   | `LOG_LEVEL` | `INFO` |

   Generate the JWT secret locally, then enter it directly in Render (for example, in PowerShell: `python -c "import secrets; print(secrets.token_urlsafe(48))"`). Never commit or share the generated value.
6. Deploy and wait for the service to become healthy. The current service origin is `https://elimuquest-api.onrender.com`.

### 3. Create the Cloudflare Pages frontend

1. In [Cloudflare Pages](https://dash.cloudflare.com/), create a Pages project and connect the existing GitHub repository. Set production branch to `main`. The current authenticated account dashboard's Pages creation route fails with module-script loading errors; no Pages project has been created yet.
2. Configure the build:

   | Setting | Value |
   |---|---|
   | Framework preset | None |
   | Build command | `npm ci && npx expo export --platform web` |
   | Build output directory | `dist` |
   | Root directory | `/` (repository root) |
   | Node version | `22` |

3. Add `EXPO_PUBLIC_API_URL` as a **production build environment variable** with the actual Render origin, e.g. `https://<service>.onrender.com`. Do not add credentials or secrets to this variable.
4. Leave `EXPO_BASE_PATH` unset so Expo assets and routes use the Pages site root.
5. Redeploy after setting the API variable. Cloudflare's Git integration should deploy subsequent pushes to `main` automatically.
6. Add the exact Pages origin (scheme and hostname, no path or trailing slash) to Render's `CORS_ORIGINS` and redeploy/restart the API if needed.

**Alternative:** The existing GitHub Pages workflow is retained. It needs the repository Actions variable `EXPO_PUBLIC_API_URL`, Pages configured to use **GitHub Actions**, and uses the `/elimuquest` base path. GitHub currently reports that Pages requires upgrading the plan or making this private repository public; do not make it public or incur a charge. Cloudflare Pages remains the preferred option because it avoids the GitHub project-site subpath.

## Verification checklist

Do not treat a successful build as a successful deployment. Use only synthetic accounts and record no passwords, tokens, or private learner data.

1. Confirm `https://<service>.onrender.com/health` returns HTTP 200 with `{"status":"ok"}`.
2. Confirm `https://<service>.onrender.com/readiness` returns HTTP 200 with `{"status":"ready"}`. This checks database connectivity.
3. Open the Cloudflare Pages HTTPS URL. Confirm browser Network requests target the Render HTTPS origin and CORS preflight/API calls succeed.
4. Register a synthetic user, log in, then verify authenticated `GET /api/v1/me` succeeds and an unauthenticated protected request returns 401.
5. Verify the registration persists by logging in again after the API service restarts. Do not use SQLite on Render; its filesystem is ephemeral.
6. Open a nested route directly and refresh it to confirm SPA routing and assets work.
7. Check Render logs, browser console, and Network panel for errors. Do not include secrets or authorization headers in diagnostics.

## Important fresh-database limitation

`alembic upgrade head` creates the schema only. It does **not** create curriculum catalog rows, approved lessons, or an administrator account. The existing `python -m app.seed` is deliberately restricted to development and inserts demo content. The importer requires mapped subject rows and saves content as drafts; it does not approve or publish lessons.

Therefore, a new hosted database can support health checks and synthetic student registration/login after migrations, but the normal learner curriculum will be empty until an audited, production-safe catalog/content bootstrap and trusted administrator provisioning process exists. Do not change `APP_ENV` to development, run the development seed on the hosted database, fabricate API responses, or publish unreviewed content to work around this limitation.

## Free-plan limitations and real-data warning

Plan details change; confirm them in the provider dashboards before creating resources. As checked against provider documentation on 2026-10-29:

- **Cloudflare Pages Free:** static frontend hosting; documented limits include 500 builds/month, one concurrent build, 20-minute build timeout, and 20,000 files per site.
- **Render Free Web Service:** sleeps after 15 minutes without inbound traffic and can take about a minute to wake. Its local filesystem is ephemeral. Free instances are documented for testing/hobby use, not production.
- **Neon Free:** currently lists 1 GB storage per project, 100 compute-hours per project, 5 GB public network transfer per project, and scale-to-zero after inactivity. Free plan projects have a limited recovery/history window and no scheduled backups.
- **Render Free Postgres is not used:** it expires after 30 days, has no backups, and is deleted after its 14-day upgrade grace period.

This arrangement is for a limited technical preview with synthetic data, not a dependable real-student service. The Phase Six beta gate documents outstanding educational review, source-rights evidence, child-data safeguards, rate limiting, backup/recovery, operational readiness, and other blockers. Obtain qualified review and close the beta gate before collecting real student or teacher data.
