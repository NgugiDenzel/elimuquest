# Project handover

## Application and actual stack

ElimuQuest is a student learning frontend built with Expo SDK 58, React Native, TypeScript, Expo Router, React Query, Zustand, and local demonstration data. It is a shared mobile/web codebase. The root git commit is `b2fb109`; the app/UI was developed locally and was not committed at the time of this handover.

## Existing structure and routes

- `app/(auth)/`: welcome, login, and register presentation.
- `app/(tabs)/`: home, practice, progress, leaderboard, profile, subjects, learning path, and lesson.
- `src/features/home` and `src/features/progress`: main screen implementations.
- `src/data/mockData.ts`: static subjects, activity, progress, review topics, and leaderboard.
- `src/components`: small shared layout and stats components.
- `backend/`: a newly started FastAPI package, SQLAlchemy model foundation, configuration, dependency manifest, Dockerfile, and Alembic config. It did not exist in the original frontend.
- `infra/docker-compose.yml`: local Postgres service definition; Docker is unavailable in this environment.

## Verified working before backend work

- Expo web server at `http://localhost:8081` and the home dashboard rendered in browser.
- Home/progress routes and tab navigation were exercised in browser.
- `npm run typecheck` and `npx expo export --platform web --output-dir dist` passed after the UI refinement. TypeScript is run with a larger Node stack due to a compiler stack overflow using the default stack.

## Existing but incomplete

- Login and registration screens were presentational and navigated directly into tabs without authentication.
- Subject detail, learning path, lesson, and practice routes were placeholders.
- Leaderboard, profile, dashboard metrics, subject cards, progress charts, goals, and streaks used static sample values.
- Buttons such as continue lesson and notifications had no backend action.

## Backend, database, and authentication status

The backend uses FastAPI, synchronous SQLAlchemy 2.x, Alembic, password hashing, and signed bearer tokens. SQLite is supported for local/test operation; PostgreSQL is the deployment target. Demo lesson content is fictional, non-official content. Registration is student-only. A role-protected lesson listing supports admin review, but no admin UI or content authoring flow exists.

Authentication tokens are planned for Expo SecureStore on native clients and browser local persistence on web. `EXPO_PUBLIC_API_URL` will configure the API base URL; physical-device use must set it to a LAN-accessible server address rather than localhost.

## Environment and limitations

Python 3.14.8 and backend dependencies are available. Docker and `psql` are not installed, and no hosted PostgreSQL or production credentials are configured. Do not claim PostgreSQL or mobile-device end-to-end verification from this environment.

## Integration map

See [frontend-backend-integration-map.md](./frontend-backend-integration-map.md).

## Next steps

1. Configure a real PostgreSQL instance and production auth/security policies before deployment.
2. Add content authoring and moderation workflows if administrators need to manage curriculum in-app.
3. Complete the dedicated practice flow, notifications, review scheduling, and account deletion as product requirements are defined.

The vertical slice and its browser/API flow are implemented. See [verification-baseline.md](./verification-baseline.md) for the checks that passed and the environment limitations.

The curriculum expansion adds the requested three level catalogues, level isolation, draft import/review workflow and learner selection. It does **not** yet include reviewed lesson content. See [curriculum-implementation-report.md](./curriculum-implementation-report.md) for verified scope and curriculum blockers.
