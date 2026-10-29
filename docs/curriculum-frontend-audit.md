# Curriculum and frontend audit

Audit performed 2026-10-24 before curriculum implementation. Baseline: `backend` pytest passed (6 tests), Ruff passed, TypeScript passed, and Expo web export succeeded.

## Existing architecture

- Frontend: Expo SDK 58, React Native, TypeScript, Expo Router. Styling uses React Native `StyleSheet` and shared tokens in `src/theme.ts`; there is no component-library dependency.
- Data access: `src/services/api/client.ts`, React Query, Zustand auth state, SecureStore on native and AsyncStorage on web.
- Backend: FastAPI, synchronous SQLAlchemy 2.x, Alembic, Pydantic, JWT bearer auth, Argon2 password hashing.
- Local database: SQLite configured in `backend/.env.example`; hosted configuration targets PostgreSQL. Tests use in-memory SQLite.

## Learner routes and APIs

- Auth: `app/(auth)/login.tsx`, `register.tsx`; `/api/v1/auth/{login,register}`, `/api/v1/me`.
- Dashboard: `app/(tabs)/index.tsx`, `src/features/home/HomeScreen.tsx`; `/api/v1/dashboard`.
- Catalogue and subject details: `app/(tabs)/subjects/[subjectId].tsx`; `/api/v1/subjects`, `/api/v1/subjects/{id}`.
- Learning path: `app/(tabs)/learning-path/[subjectId].tsx`; `/api/v1/subjects/{id}/learning-path`.
- Lesson: `app/(tabs)/lesson/[lessonId].tsx`; lesson, session, answer, and completion endpoints.
- Progress, practice discovery, leaderboard, profile: `app/(tabs)/progress.tsx`, `practice.tsx`, `leaderboard.tsx`, `profile.tsx`; progress, leaderboard and profile APIs. Dedicated mixed/topic practice is not implemented.

## Data and security

- Existing entities: users, subjects, topics, lessons, multiple-choice questions, sessions, attempts, lesson progress, XP, daily activity and achievements.
- Curriculum system and level fields, structured lesson material/provenance and a separate content workflow are being added in the current implementation.
- Existing student flow supports registration/login, published-only lesson retrieval, server grading, one answer per question/session and idempotent XP awards.
- There is a protected admin lesson listing, but no authoring, review, import, publication workflow, or admin UI.
- `Subject.slug` and `Subject.code` are globally unique. Subjects have no curriculum-system/level identity. `User.form` is an unvalidated free-form string.
- Lessons have a Boolean `published` flag only. There is no curriculum provenance, outcomes/objectives, content version, review state, structured explanation or author/reviewer record.
- Existing seed data is explicitly fictional and has no verified learning-outcome mapping. It must not be presented as official curriculum content.

## Current UX issues

- Learners cannot select or confirm curriculum system and grade/form; `form` defaults to Form 4.
- Catalogue is not scoped to a learner's level, so a future shared catalogue would risk cross-level content leakage.
- Subject and lesson pages are functional but sparse; no objective, worked-example, outcome, or structured section support exists.
- Empty/error/loading handling exists in several screens. Existing React Native layout and theme provide a sound base; do not replace the routing or styling stack.

## Gaps and implementation sequence

1. Curriculum identities, validated subject mappings and level-scoped learner endpoints.
2. Structured lesson provenance and draft/review/approval/publication states.
3. Versioned package schema with a dry-run/idempotent importer and overwrite protection.
4. Learner level selection, admin review actions, and structured objective/example display.
5. Research actual Grade 6 and Form 4 design PDFs and extract page-level references; do not add topics until that work is complete.
6. Test mapping isolation, workflow, importer safety and existing lesson/auth/reward behavior; browser-check selection and completion.

## Regression risks

- Globally unique legacy subject identifiers need backwards-compatible migration handling if the same official subject appears at multiple levels.
- Existing registration must remain usable while a learner's curriculum is selected.
- Subject, dashboard, progress and next-lesson queries must all apply the same curriculum/level boundary.
- Old published seed content has no verified curriculum mapping; it must remain labelled legacy/demo and never be silently reclassified.
- Published answer keys and server-side grading/idempotent rewards must not regress.
