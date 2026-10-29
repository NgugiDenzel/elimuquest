# ElimuQuest

A cross-platform learning app for Kenyan secondary school students built with Expo, React Native, and TypeScript.

## Features

- Student dashboard with XP, streak, and daily goals
- Subject cards and lesson navigation
- Curriculum-aware subject catalogues for Grade 6, Grade 9 and Form 4
- Progress analytics and mastery overview
- Practice, leaderboard, and profile views

## Run locally

```bash
npm install
npm run web -- --port 8081
```

In a second terminal, start FastAPI from the backend directory:

```powershell
cd C:\Users\Admin\Desktop\elimuquest\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Keep both processes running. Check `http://localhost:8000/health` returns `{"status":"ok"}`, then open the web app. Use `npm start` instead to select a native Expo target.

For web specifically, run `npx expo start --web --port 8081` and open `http://localhost:8081`.

The FastAPI server must also be running at `http://localhost:8000`; otherwise login and registration cannot connect. The browser reports connection failures separately from API HTTP errors. See [backend setup](./backend/README.md) for run commands, phone/LAN access, and exact CORS configuration.

## Backend

See [backend setup](./backend/README.md). The backend uses FastAPI, SQLAlchemy, Alembic, and a PostgreSQL deployment target. The current local SQLite database is in `backend/elimuquest.db`; do not rerun seeding or migrations against an existing database as part of ordinary startup. In development, the client discovers the browser or Expo host automatically. Physical devices need LAN access and may need an explicit `EXPO_PUBLIC_API_URL`; see the backend guide for bind and CORS details.

## Web preview on GitHub Pages

The GitHub Actions workflow in `.github/workflows/pages.yml` exports the Expo web app and publishes it at `https://ngugidenzel.github.io/elimuquest/`. Expo Router uses a single-page export with a Pages `404.html` fallback for routes such as lessons. The app config uses `/elimuquest` as its base path only when `EXPO_BASE_PATH` is set by the Pages workflow; local development keeps the root path.

Before enabling Pages, deploy the FastAPI backend to an HTTPS host, set the repository Actions variable `EXPO_PUBLIC_API_URL` to the backend origin (without `/api/v1`), and configure the backend's exact CORS origin as `https://ngugidenzel.github.io`. In GitHub repository **Settings → Pages**, select **GitHub Actions** as the build and deployment source. The workflow skips its build until the API URL variable is configured.

GitHub Pages serves a public website. Do not enter real learner data or invite learners until the outstanding content-rights, educational-review, privacy, security, and operations blockers in [the Phase Six beta gate](./docs/PHASE_SIX_REGRESSION_BETA_GATE.md) are closed. The app is not currently approved for an external learner beta.

## Current scope

The initial integrated backend provides student registration/login, profile retrieval, dashboard/subjects/learning paths, lesson sessions and server-graded answers, completion with idempotent XP/progress, progress summaries, and a privacy-conscious leaderboard. See [the handover report](./docs/project-handover.md) and [integration map](./docs/frontend-backend-integration-map.md) for verified coverage and remaining work.

Curriculum subject names and levels are mapped from the KICD design listings. Topic/outcome content remains unavailable until its exact design PDF is cited and reviewed. See the [source register](./docs/curriculum-source-register.md), [coverage matrix](./docs/curriculum-coverage-matrix.csv), and [structured content importer](./backend/content-packages/README.md).

The supplied Grade 6 Mathematics Pupil’s Book excerpt has been imported as five draft lessons with 20 practice-derived quiz items for Strand 1: Numbers, Sub-strand 1.1: Whole Numbers. These lessons stay hidden from ordinary learners until an authorized reviewer approves and publishes them. The provided excerpt does not contain its referenced answer key; quiz keys are calculated independently and flagged for reviewer verification.
