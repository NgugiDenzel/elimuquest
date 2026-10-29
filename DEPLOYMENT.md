# ElimuQuest deployment handover

**Status:** Not deployed. No Cloudflare, Render, or Neon service was created from this checkout.
**Target:** A synthetic-data technical preview using Cloudflare Pages, Render Free, and Neon Free.
**Do not invite real learners:** The existing Phase Six beta gate is not ready for real student data.

## What is already configured

- The Expo web build is `npx expo export --platform web`; the output directory is `dist`.
- `app.config.js` uses a single-page web export. Leave `EXPO_BASE_PATH` unset on Cloudflare Pages; the Pages site is served from the domain root.
- The frontend reads `EXPO_PUBLIC_API_URL` at build time. Set it to the HTTPS API origin only, without `/api/v1` or a trailing slash. It is public client configuration, not a secret.
- The FastAPI entry point is `app.main:app` and its readiness endpoint is `/readiness`.
- `backend/pyproject.toml` includes FastAPI, Uvicorn, SQLAlchemy, Alembic, and psycopg 3. The models and migrations use SQLAlchemy types supported by PostgreSQL.
- `backend/Dockerfile` binds Uvicorn to Render's `PORT` (with local fallback `8000`). A Render start-command override is required to apply Alembic migrations before starting the API.
- The database is configured with `DATABASE_URL`; production settings reject the default local SQLite URL and the development JWT secret.

## Configure the services

Use the same region for Render and the Neon project where practical. Do not copy the repository's SQLite database to a hosted service.

### 1. Create a Neon database

1. Sign in to [Neon](https://console.neon.tech/) and create a project on the **Free** plan.
2. Keep the database private to the application connection. Copy its connection string from the Neon dashboard; do not put it in Git, a frontend variable, or chat.
3. Configure Render's `DATABASE_URL` with that connection string using the SQLAlchemy psycopg driver prefix:

   ```text
   postgresql+psycopg://...
   ```

   Preserve the generated hostname, database, URL-encoded credentials, and TLS query parameters from Neon. Do not use a local SQLite path.

### 2. Create the Render API

1. In [Render](https://dashboard.render.com/), create a **Web Service** from `NgugiDenzel/elimuquest`.
2. Set **Root Directory** to `backend`, runtime to **Docker**, and Dockerfile path to `Dockerfile`. Choose **Free** only for this synthetic-data preview.
3. Set the Docker command to run migrations and then Uvicorn on Render's assigned port:

   ```sh
   /bin/sh -c 'alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"'
   ```

   Keep this service to one instance while migrations are run at startup.
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
6. Deploy and wait for the service to become healthy. Record the assigned HTTPS origin as `https://<service>.onrender.com`.

### 3. Create the Cloudflare Pages frontend

1. In [Cloudflare Pages](https://dash.cloudflare.com/), create a Pages project and connect the existing GitHub repository. Set production branch to `main`.
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

**Alternative:** The existing GitHub Pages workflow is retained. It needs the repository Actions variable `EXPO_PUBLIC_API_URL`, Pages configured to use **GitHub Actions**, and uses the `/elimuquest` base path. Cloudflare Pages is the recommended path here because it avoids the GitHub project-site subpath.

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
