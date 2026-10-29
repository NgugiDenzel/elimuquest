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

## Current scope

The initial integrated backend provides student registration/login, profile retrieval, dashboard/subjects/learning paths, lesson sessions and server-graded answers, completion with idempotent XP/progress, progress summaries, and a privacy-conscious leaderboard. See [the handover report](./docs/project-handover.md) and [integration map](./docs/frontend-backend-integration-map.md) for verified coverage and remaining work.

Curriculum subject names and levels are mapped from the KICD design listings. Topic/outcome content remains unavailable until its exact design PDF is cited and reviewed. See the [source register](./docs/curriculum-source-register.md), [coverage matrix](./docs/curriculum-coverage-matrix.csv), and [structured content importer](./backend/content-packages/README.md).

The supplied Grade 6 Mathematics Pupil’s Book excerpt has been imported as five draft lessons with 20 practice-derived quiz items for Strand 1: Numbers, Sub-strand 1.1: Whole Numbers. These lessons stay hidden from ordinary learners until an authorized reviewer approves and publishes them. The provided excerpt does not contain its referenced answer key; quiz keys are calculated independently and flagged for reviewer verification.
