# API contract overview

The FastAPI OpenAPI document is available at `/openapi.json` and the interactive API reference at `/docs` while the backend is running.

All `/api/v1` routes except registration and login require an `Authorization: Bearer <access_token>` header unless noted. Error responses use FastAPI's standard JSON `detail` field. Identifiers exposed to the app are stable slugs or opaque session IDs.

| Method | Route | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Create a student account and return an access token and profile |
| `POST` | `/api/v1/auth/login` | Authenticate and return an access token and profile |
| `GET` | `/api/v1/me` | Return the authenticated profile |
| `PATCH` | `/api/v1/me/profile` | Update supported profile fields |
| `GET` | `/api/v1/subjects` | List subjects |
| `GET` | `/api/v1/subjects/{subject_id}` | Get a subject |
| `GET` | `/api/v1/subjects/{subject_id}/learning-path` | List its topics and published lessons |
| `GET` | `/api/v1/lessons/{lesson_id}` | Get a published lesson without answer keys |
| `POST` | `/api/v1/lesson-sessions` | Start a session for a published lesson |
| `POST` | `/api/v1/lesson-sessions/{session_id}/answers` | Submit one answer per question and receive grading feedback |
| `GET` | `/api/v1/lesson-sessions/{session_id}` | Read the authenticated student's session |
| `POST` | `/api/v1/lesson-sessions/{session_id}/complete` | Complete a fully answered session; rewards are idempotent per session |
| `GET` | `/api/v1/dashboard` | Return dashboard metrics and next-lesson data |
| `GET` | `/api/v1/progress` | Return lesson, subject, and accuracy progress |
| `GET` | `/api/v1/leaderboard` | Return the student leaderboard |
| `GET` | `/api/v1/curricula` | Return curriculum/level choices and mapped official subject names |
| `GET` | `/api/v1/admin/lessons` | Admin-only listing, including unpublished lessons |
| `PATCH` | `/api/v1/admin/lessons/{lesson_id}/status` | Admin-only review/publication state transition |

Lesson completion awards `10 + 5 × correct answers` XP and stores one XP ledger transaction per session. Students cannot fetch unpublished lessons or correct-answer fields. Admin role assignment is an operator responsibility; public registration cannot assign roles.

Subject, learning-path, lesson, dashboard and mastery responses are scoped to the authenticated student's selected curriculum and level. `PATCH /api/v1/me/profile` accepts `curriculum_system` and `curriculum_level` together; supported selections are `CBC_CBE` / `Grade 6`, `CBC_CBE` / `Grade 9`, and `8_4_4` / `Form 4`. Grade 6 science is listed as Science & Technology, Grade 9 science as Integrated Science; neither is split into standalone Chemistry/Physics subjects.

Content import schema and sample package are documented in [backend/content-packages/README.md](../backend/content-packages/README.md). Imports create drafts only; admin review must precede publication.

The browser client reads `EXPO_PUBLIC_API_URL` from the repository root environment. See [backend/README.md](../backend/README.md) for backend setup and production configuration requirements.
