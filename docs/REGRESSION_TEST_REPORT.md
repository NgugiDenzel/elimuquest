# Regression and validation report — 2026-10-29

## Repository checks

Commands were run from their correct project directories after the content import:

| Command | Result |
|---|---|
| `cd backend; python -m pytest -q` | Passed: 20 tests; one Starlette/httpx deprecation warning |
| `cd backend; python -m ruff check app tests` | Passed: all checks passed |
| `npx tsc --noEmit` | Passed |

At the time of the earlier Phase Three checks, no frontend lint configuration existed. During Phase Four, `npx expo lint` automatically installed ESLint and created `eslint.config.js`, but the Expo command then failed its ESLint-version check. Running `npx eslint .` directly reported one existing `react-hooks/set-state-in-effect` error in `src/providers/AuthProvider.tsx:31` and 26 warnings. This auth-provider issue predates the curriculum changes and was not modified. The Expo frontend export and TypeScript check passed.

## Content package and import checks

- Both new package files passed the existing content importer dry-run: 3 lessons eligible in each, no validation errors.
- Import used the existing `import_content` service, with both packages in a single transaction. Six lessons, two topics, and 18 questions were created as drafts.
- Repeating the importer dry-run reported `created=0`, `unchanged=3` for each package.
- All multiple-choice answers match a listed option, explanations are present, options are unique, and the question schema validated. No numerical marking keys were introduced.
- Database checks found zero duplicate lesson slugs or duplicate question IDs.
- SQLite `PRAGMA integrity_check` returned `ok` for both the active database and its pre-import backup.

## API and live service checks

- `http://localhost:8000/health` returned `{"status":"ok"}`.
- `http://localhost:8000/readiness` returned `{"status":"ready"}`.
- `http://localhost:8081` returned HTTP 200.
- The full backend API test suite passed, including existing authentication, publication filtering, lesson access, quiz grading, progress, and XP persistence tests.
- At initial import, the six records remained drafts and were excluded from learner endpoints until the authorized admin review and publication steps below. No authentication or publication bypass was used.

### Post-publication learner verification

After an authorized admin used the existing status workflow to publish the six lessons:

- The authenticated Grade 6 dashboard showed English with “Next up · Reading for main ideas” and Science & Technology with “Next up · Plant parts and their functions.”
- English subject detail reported 3 published lessons; its learning path listed all three lessons.
- Science & Technology learning path listed all three lessons.
- Opened the English Reading for main ideas lesson and the Science Plant parts and their functions lesson. Each rendered its learning content and first multiple-choice quiz question/options.
- Unauthenticated direct requests to the new lesson endpoints returned HTTP 401 before admin authentication, confirming auth remains required.
- No quiz answer was submitted, so the verification did not create an attempt or XP award.

## Data preservation

The active database counts changed only for topics (+2), lessons (+6), and questions (+18). Users, attempts, progress, sessions, XP transactions, achievements, user achievements, and daily activity rows were compared against the pre-import SQLite backup; every table's rows were identical.

## Notes

The initial inventory's tests also passed before the import. The only observed test warning is the existing Starlette/httpx `TestClient` deprecation notice. The previous report's claims about Ruff and publication state were re-run or corrected based on actual results.

## Phase Four expansion and publication — 2026-10-29

### Pre-import safety and importer

- Verified `backend/backups/elimuquest-phase4-20261029-122116.db` before writing. It was 376,832 bytes, opened successfully, returned `PRAGMA integrity_check = ok`, and had 43 topics, 51 lessons and 227 questions, matching the active pre-import database.
- All eight new packages passed the existing importer dry-run. One atomic import created 8 topics, 16 draft lessons and 48 questions. Second dry-runs returned 0 created and 2 unchanged per package.
- The authenticated publication preview reported 16 eligible and one blocked pre-existing Biology demo. The authenticated endpoint published the 16 eligible lessons. Re-import after publication still reported all 16 unchanged.
- Database checks: 17 subjects, 51 topics, 67 lessons, 275 questions; 66 published and one blocked draft; no in-review/approved/archived records. No duplicate lesson slugs or question IDs.
- SQLite integrity was `ok` after publication. Counts and stable hashes for all user/account/history tables matched the backup exactly: users 2, attempts 37, progress 10, sessions 28, XP transactions 14, achievements 1, user achievements 2, daily activity 3.

### Publication regression discovered and fixed

The first live bulk publication left the blocked `cell-structure` demo in `in_review`: the endpoint transitioned a draft before checking its required explanation sections. The record was restored to draft with the authorized status API. The endpoint now validates each lesson before any transition; `test_admin_bulk_publish_leaves_blocked_drafts_unchanged` covers this and confirms the record remains an unpublished draft. No other blocked or eligible lesson was left in review.

### Live/API behavior

- `http://localhost:8000/health` returned `{"status":"ok"}`; frontend `http://localhost:8081` returned HTTP 200.
- Using the existing authenticated account with admin role and Grade 6 curriculum profile, `/subjects` returned the supported Grade 6 subjects, and the Kiswahili learning path returned the two newly published lessons. This verified the learner-facing route and curriculum filter, not a student-role login.
- Unauthenticated direct retrieval of a newly published lesson returned HTTP 401. Learner endpoints still filter by curriculum and published state; no draft endpoint exposure was introduced.
- Navigation verification did not submit answers or change attempts, progress, sessions or XP.

### Latest automated checks

| Command | Result |
|---|---|
| `cd backend; python -m pytest -q` | 21 passed; existing Starlette/httpx deprecation warning |
| `cd backend; python -m ruff check app tests` | Passed |
| `npx tsc --noEmit` | Passed |
| `npx expo export --platform web` | Passed; web bundle exported to `dist` |
| `npx expo lint` | Failed after auto-setup; Expo CLI reports an ESLint version check failure despite installing ESLint 9 |
| `npx eslint .` | Failed on one pre-existing auth-provider hook lint error; 26 warnings; no curriculum files implicated |
| All-package importer dry-run + repeat dry-run | Passed; 16 eligible, then 16 unchanged |

Official curriculum alignment of the new material remains unverified. This is supplementary starter content and needs independent subject-expert review. No production deployment was run. See the content expansion report and source register for the OpenStax licensing blocker.

## API connection error investigation — 2026-10-29

- Reproduced the reported registration failure in the browser: `POST http://localhost:8000/api/v1/auth/register` failed with `net::ERR_CONNECTION_REFUSED`. Browser history showed the same failure for login, `/health`, and `/api/v1/curricula`.
- At the time of reproduction, port 8081 had a listener but port 8000 did not; PowerShell requests to both `http://localhost:8000/health` and `/readiness` were actively refused. This is a stopped/unavailable backend, not an HTTP, authentication, CORS, or SQLAlchemy exception.
- Started Uvicorn from the `backend` working directory on `0.0.0.0:8000`. Health and readiness returned HTTP 200 (`ok` and `ready`). A preflight from `http://localhost:8081` returned 200 with the expected CORS origin and methods.
- The frontend's catch-all previously converted all non-HTTP errors into “Could not reach the server,” masking transport vs timeout vs invalid-response details. It now distinguishes connection errors, timeouts, HTTP status errors, malformed API responses, and unexpected client errors without showing raw exception details.
- Development web builds derive the API host from the browser hostname; Expo native development derives it from the documented `Constants.expoConfig.hostUri`. An explicit `EXPO_PUBLIC_API_URL` still overrides both. Non-development builds without the variable report configuration missing rather than calling localhost.
- Backend startup instructions now state the required bind host for browser vs phone use, the need to keep Uvicorn running, and exact-origin CORS configuration. Routine startup documentation no longer instructs seeding the existing database.
- Frontend tests: `npm test` passed (4 tests covering connection refusal, HTTP 401, timeout and invalid JSON).
- Backend tests: `cd backend; python -m pytest -q` passed (21 tests; one pre-existing Starlette/httpx deprecation warning); Ruff passed.
- `npx tsc --noEmit` passed. `npx expo export --platform web` passed.

## Curriculum coverage expansion — 2026-10-29

### Import, publication and data integrity

- The importer validated 26 new package files containing 58 lessons and 174 questions; one transaction imported 26 topics, 58 draft lessons and 174 questions.
- Repeat dry-run after import and publication returned `created=0`, `unchanged=58`.
- Authenticated publication preview returned 58 eligible and one blocked pre-existing demo. The supported authenticated workflow published 58 and left the blocked `cell-structure` draft unchanged.
- Final SQLite state: 17 subjects, 77 topics, 125 lessons, 124 published lessons, 449 questions, and one blocked draft. SQLite integrity returned `ok`; duplicate lesson slugs and question IDs were both zero.
- The verified pre-import backup is `backend/backups/elimuquest-coverage-expansion-20261029-134721.db` (430,080 bytes; integrity `ok`). Full row hashes match it for users, attempts, progress, sessions, XP, achievements, user achievements and daily activity.
- Learner preservation counts match the backup: 2 users, 37 attempts, 10 progress rows, 30 sessions, 14 XP transactions, 1 achievement, 2 user achievements and 3 daily activities. A temporary test password and profile were restored; the one uncompleted test-created session was removed after confirming it had no attempts.

### Learner API and web UI

- Using a student-role account, Grade 6 English and Science & Technology, Grade 9 Integrated Science and Kiswahili, and 8-4-4 Form 4 Chemistry and Physics learning paths each returned eight published lessons. Each representative lesson detail included three questions.
- A Grade 6 lesson requested while the learner was selected to another curriculum returned 404, confirming curriculum filtering.
- Browser UI verified with the student role: Grade 6 English listed all eight lessons and opened a new lesson displaying objectives, explanation, recap and a quiz item/options. Grade 9 Integrated Science and Form 4 Chemistry subject and learning-path screens displayed the eight published lessons. No answer was submitted.
- Live `/health` returned `{"status":"ok"}` and the frontend at `http://localhost:8081` served the app. No production deployment occurred.

### Latest automated checks

| Command | Result |
|---|---|
| `cd backend; python -m pytest -q` | 22 passed; one existing Starlette/httpx `TestClient` deprecation warning |
| `cd backend; python -m ruff check app tests` | Passed |
| `npm test` | 4 passed |
| `npx tsc --noEmit` | Passed |
| `npx expo export --platform web` | Passed; Metro discarded an unreadable stale cache and completed a full crawl |
| Coverage package schema/structure checks | Passed; 26 packages, 58 unique lessons, 174 questions, required explanations/examples/recaps |
| Importer dry-run / apply / repeat dry-run | Passed; 58 created as drafts, then 58 unchanged |
| Authenticated review preview / publication | Passed; 58 published, one blocked draft preserved |

Official curriculum alignment remains unverified; content awaits independent subject-expert review. The source register records the limited factual cross-check sources and their license constraints. No source text or questions were copied. The OpenStax restrictions and previously documented Grade 6 Biology source licensing issue remain public-release review items.

## Phase Five quality and readiness audit — 2026-10-29

### Database and content audit

- Read-only baseline and post-audit counts match: 17 subjects, 77 topics, 125 lessons, 124
  published lessons, one draft, and 449 questions. There are no archived, in-review, or
  approved records.
- The database has 13 supported subject/curriculum/level combinations: five 8-4-4 Form 4,
  four CBC/CBE Grade 6, and four CBC/CBE Grade 9 offerings. Four `LEGACY/Legacy` demo
  subjects are not supported learner selections and are not mapped to Grade 10 or Form 4.
- Automated structural review covered all 125 lesson records and 449 questions. It found
  45 lessons without learning objectives, four without explanation sections, 80 without a
  lesson-level source locator, three published demo lessons without reviewer metadata,
  and 201 short-answer questions without explanatory feedback. No lessons lack questions;
  no topics are empty; no publication-state mismatches, duplicate lesson slugs, or
  foreign-key violations were found.
- One exact prompt, “Find the mode.”, occurs in Grade 6 Data Handling and legacy Form 4
  Statistics II. Each lesson has a different dataset; the respective answer keys (4 and 6)
  are consistent with those datasets.
- Nine numerical answers across those two lessons were recalculated. This limited spot
  check does not constitute a full subject-expert review. Accuracy, language, and level
  suitability of all other published content remain unaudited.
- The generated, repeatable audit artifacts are
  `PHASE_FIVE_CONTENT_AUDIT.csv`, `PHASE_FIVE_QUESTION_AUDIT.csv`,
  `PHASE_FIVE_CURRICULUM_COVERAGE.csv`, and
  `PHASE_FIVE_SOURCE_AND_LICENSING_REGISTER.csv`.
- Existing importer dry-runs reported 26 expansion packages / 58 unchanged lessons, 36
  Mathematics packages / 36 unchanged lessons, and the Grade 6 pupil-book package / five
  unchanged lessons. No import apply or publication change was performed.

### Backup and learner-data verification

- Created and integrity-checked
  `backend/backups/elimuquest-phase5-20261029-153833.db` (716,800 bytes).
- Active database and backup both return `ok` for `PRAGMA integrity_check` and zero rows
  for `PRAGMA foreign_key_check`.
- An isolated SQLite backup-API restore passed integrity/FK checks and matched counts.
- Stable row hashes match between active DB and backup for users (2), answer attempts (37),
  progress (10), lesson sessions (30), XP transactions (14), achievements (1), user
  achievements (2), and daily activity (3). No learner records were changed.

### Regression and configuration changes

- Fixed the `react-hooks/set-state-in-effect` error by deferring initial auth restoration
  outside the synchronous effect call path. Added two focused AuthProvider tests.
- Added API regression coverage for empty answer validation, an unknown question, and
  incomplete lesson completion; current rules continue to reject incomplete sessions.
- Production Docker configuration now selects `APP_ENV=production` and rejects the local
  development JWT secret or default SQLite URL. Local Compose now requires a non-empty
  environment-supplied database password and binds the database port to loopback.
- Historical connectivity evidence identifies backend connection refusal while no
  process listened on port 8000. In this audit, ports 8000 and 8081 responded, health and
  readiness returned 200, and the browser CORS preflight succeeded. The authenticated
  learner UI was not repeated; the shared browser page was at `/welcome`.

### Final Phase Five checks

| Command / verification | Result |
|---|---|
| `cd backend; python -m pytest -q` | 27 passed; one Starlette/httpx deprecation warning |
| `cd backend; python -m ruff check app tests scripts` | Passed |
| `npm test -- --runInBand` | 6 passed |
| `npx tsc --noEmit` | Passed |
| `npx expo lint` | 0 errors; 27 warnings remain outside the fixed hook error |
| `npx expo export --platform web` | Passed |
| `npm audit --omit=dev --json` | 19 advisories: 5 high, 7 moderate, 7 low; not remediated |
| `npx expo install --check` | Could not complete because the registry connection reset (`ECONNRESET`) |
| Python advisory scan | `pip-audit` not installed |
| Docker Compose validation | Not run; Docker CLI unavailable |

Phase Five readiness is **NOT READY** for external learners pending dependency remediation,
content expert review, source rights review, child-data/privacy controls, production
operations, and a repeated authenticated learner-journey test. No deployment occurred.
The installed Expo is 58.0.17 while direct dependencies include `expo-constants` 17.0.8
and Expo Router 4.0.22. Their SDK 58 compatibility could not be verified because the
compatibility check was blocked by the registry connection failure; no dependency upgrade
was attempted.
