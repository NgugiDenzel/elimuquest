# Frontend/backend integration map

The app is an Expo SDK 58 React Native project using Expo Router. It has no existing backend, auth provider, API client, or query client. The screens below were inspected before implementation.

| Frontend feature | Existing implementation | Required API | Integration status |
| --- | --- | --- | --- |
| Sign up / sign in | `app/(auth)/register.tsx`, `app/(auth)/login.tsx` | `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/me` | Connected |
| Home | `src/features/home/HomeScreen.tsx` | `GET /api/v1/dashboard` | Connected |
| Subjects | Subject cards and detail route | `GET /api/v1/subjects`, `GET /api/v1/subjects/{id}` | Connected |
| Learning path | `app/(tabs)/learning-path/[subjectId].tsx` | `GET /api/v1/subjects/{id}/learning-path` | Connected |
| Lesson and answers | `app/(tabs)/lesson/[lessonId].tsx` | `POST /api/v1/lesson-sessions`, `POST /api/v1/lesson-sessions/{id}/answers`, `POST /api/v1/lesson-sessions/{id}/complete` | Connected; browser-verified |
| Progress | `src/features/progress/ProgressScreen.tsx` | `GET /api/v1/progress` | Connected; browser-verified |
| Practice | `app/(tabs)/practice.tsx` | Practice-session API | Subject discovery connected; dedicated practice flow not implemented |
| League | `app/(tabs)/leaderboard.tsx` | `GET /api/v1/leaderboard` | Connected |
| Profile | `app/(tabs)/profile.tsx` | `GET /api/v1/me`, `PATCH /api/v1/me/profile` | Connected |
| Notifications | Home notification icon has no action | Requires product/service decision | Not implemented |
| Curriculum selection | Home dashboard | `GET /api/v1/curricula`, `PATCH /api/v1/me/profile` | Connected; selection scopes learner content |
| Administration | `app/(tabs)/admin.tsx` (admin-only profile link) | `GET /api/v1/admin/lessons`, `PATCH /api/v1/admin/lessons/{id}/status` | Protected review/publication UI; content authoring uses JSON importer |

## Initial scope and decisions

- Use FastAPI with synchronous SQLAlchemy 2.x and Alembic. A single request-scoped database session keeps the initial service straightforward.
- Use PostgreSQL in hosted environments and Docker Compose; allow SQLite for local smoke tests and unit tests.
- The development seed contains clearly labelled fictional curriculum content. It is never run at application startup.
- The requested subject names are seeded as empty curriculum offerings; no topic sequence, learning outcome, or lesson is claimed until its design PDF reference is reviewed.
- Backend-managed accounts use Argon2 password hashing and short-lived signed bearer tokens. The app stores tokens in Expo SecureStore on native and browser local storage on web.
- Streak days and daily goal dates use the student's IANA timezone, defaulting to `Africa/Nairobi`.
- A lesson is one-question-attempt-per-session. Completion requires an answer for every question. A completed session is idempotent and awards one XP ledger entry.
- There is no production authentication provider or deployed PostgreSQL instance configured in this repository. Production secrets, database hosting, content review, and legal/privacy review remain deployment responsibilities.
