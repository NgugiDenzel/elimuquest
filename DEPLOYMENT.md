# ElimuQuest deployment handover

**Status (2026-10-29):** Neon Free project `elimuquest-beta` is in AWS US East 2 (Ohio). Render Free service `elimuquest-api` is live in Ohio at `https://elimuquest-api.onrender.com`; `/health` and `/readiness` return HTTP 200. The Expo frontend is live at `https://elimuquest-web.onrender.com`. Render's `CORS_ORIGINS` retains `https://elimuquest.pages.dev` and now also allows the frontend's exact origin, `https://elimuquest-web.onrender.com`; the API redeploy succeeded. A `/*` → `/index.html` rewrite is active for Expo Router routes. Synthetic registration, login, authenticated `/me`, invalid-password handling, logout, direct route loads and refresh, and CORS preflight were verified in a browser. No real learner data was entered. The service is technically reachable but the curriculum is empty and the existing Phase Six beta gate is not ready for real learners.
**Target:** A synthetic-data technical preview using Render Static Site, Render Free Web Service, and Neon Free.
**Do not invite real learners:** The existing Phase Six beta gate is not ready for real student data.

## What is already configured

- The Expo web build is `npx expo export --platform web`; the output directory is `dist`.
- `app.config.js` uses a single-page web export. Leave `EXPO_BASE_PATH` unset for the root-hosted Render static site.
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
   | `CORS_ORIGINS` | `https://elimuquest.pages.dev,https://elimuquest-web.onrender.com` |
   | `LOG_LEVEL` | `INFO` |

   Generate the JWT secret locally, then enter it directly in Render (for example, in PowerShell: `python -c "import secrets; print(secrets.token_urlsafe(48))"`). Never commit or share the generated value.
6. Deploy and wait for the service to become healthy. The current service origin is `https://elimuquest-api.onrender.com`.

### 3. Render Static Site frontend

The existing Render Static Site is named `elimuquest-web`, is connected to `NgugiDenzel/elimuquest` on branch `main`, and is publicly served at `https://elimuquest-web.onrender.com`. Its currently serving deployment uses:

| Setting | Value |
|---|---|
| Build command | `npm ci && npx expo export --platform web` |
| Publish directory | `dist` |
| Root directory | Repository root |
| Node version | `22` |

The deployment uses `EXPO_PUBLIC_API_URL=https://elimuquest-api.onrender.com`. Expo embeds this public API base URL during build; it is not a secret. The root page and JS assets have been fetched successfully over HTTPS.

**Applied and verified in the Render Dashboard:**

1. The API's `CORS_ORIGINS` preserves `https://elimuquest.pages.dev` and includes `https://elimuquest-web.onrender.com`. The environment update triggered a deployment, which reached **Live**.
2. The static site's rewrite is **Rewrite** source `/*` to destination `/index.html`. Direct `/register` and `/login` requests now return the Expo application with HTTP 200.

The existing GitHub Pages workflow is retained but is not used for this deployment. Do not make the private repository public or upgrade a plan to enable it.

## Verification checklist

Do not treat a successful build as a successful deployment. Use only synthetic accounts and record no passwords, tokens, or private learner data.

1. **Passed:** `https://elimuquest-api.onrender.com/health` returns HTTP 200 with `{"status":"ok"}`.
2. **Passed:** `https://elimuquest-api.onrender.com/readiness` returns HTTP 200 with `{"status":"ready"}`. This checks database connectivity.
3. **Passed:** browser CORS preflight from `https://elimuquest-web.onrender.com` returns HTTP 200 with that exact `Access-Control-Allow-Origin`.
4. **Passed:** synthetic registration, login, authenticated `/api/v1/me` (observed by the app), logout, login again, and invalid-password handling (HTTP 401 with a user-facing error).
5. **Passed:** `/health` and `/readiness` return HTTP 200; the readiness check verifies database connectivity. The synthetic account remained usable after logout and a subsequent login. Earlier API checks also verified persistence across a service restart. Do not use SQLite on Render; its filesystem is ephemeral.
6. **Passed:** direct `/register` and `/login` requests return HTTP 200; authenticated `/profile` loads directly and remains on that route after browser refresh.
7. **Passed:** live browser layout checks found no horizontal overflow on the profile screen at 320×568, 360×800, 390×844, 768×1024, 1024×768, 1366×768, and 1920×1080; login and registration also had no horizontal overflow at 320×568 and 1366×768.
8. **Passed:** browser resources included the production API origin; no CORS or critical app runtime error appeared during successful registration/login. The 401 recorded during the invalid-password test was expected.

## Important fresh-database limitation

`alembic upgrade head` creates the schema only. It does **not** create curriculum catalog rows, approved lessons, or an administrator account. The existing `python -m app.seed` is deliberately restricted to development and inserts demo content. The importer requires mapped subject rows and saves content as drafts; it does not approve or publish lessons.

Therefore, a new hosted database can support health checks and synthetic student registration/login after migrations, but the normal learner curriculum will be empty until an audited, production-safe catalog/content bootstrap and trusted administrator provisioning process exists. Do not change `APP_ENV` to development, run the development seed on the hosted database, fabricate API responses, or publish unreviewed content to work around this limitation.

## Free-plan limitations and real-data warning

Plan details change; confirm them in the provider dashboards. The [Render Free instance and static-site docs](https://render.com/docs/free), [Render static-site docs](https://render.com/docs/static-sites), and [Neon plan docs](https://neon.com/docs/introduction/plans) were checked on 2026-10-29:

- **Render Static Site:** the frontend uses Render's $0 static-site offering, served through a global CDN with HTTPS and Git-based deploys. Static sites use the workspace's included bandwidth and pipeline minutes; exceeding included usage can suspend service/builds without a payment method, or incur overage charges if billing is enabled.
- **Render Free Web Service:** the API uses the $0 compute plan; it sleeps after 15 minutes without inbound traffic and takes about a minute to wake. Free web services share 750 instance hours per workspace each month. Its local filesystem is ephemeral. Free instances are documented for testing/hobby use, not production. Avoid excess usage and do not upgrade or add payment details without authorization.
- The frontend API client waits up to 90 seconds for a response, so a first login or sign-up can remain in progress while the free API wakes. If that limit is reached, it now explains the likely wake delay instead of showing a generic server timeout.
- **Neon Free:** $0/month, with 100 compute-hours per project, 1 GB storage per project (20 GB account total), and 5 GB public network transfer per project. Compute scales to zero after five minutes of inactivity. The Free plan has limited recovery history and no scheduled backups; exceeding included resources may require stopping usage or choosing a paid plan.
- **Render Free Postgres is not used:** it expires after 30 days, has no backups, and is deleted after its 14-day upgrade grace period.

This arrangement is for a limited technical preview with synthetic data, not a dependable real-student service. The Phase Six beta gate documents outstanding educational review, source-rights evidence, child-data safeguards, rate limiting, backup/recovery, operational readiness, and other blockers. Obtain qualified review and close the beta gate before collecting real student or teacher data.
