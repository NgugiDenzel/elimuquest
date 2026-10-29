# Phase Six Regression Results and Beta Gate

**Decision:** **NOT READY for beta**  
**Deployment:** Not performed

## Regression results

| Check | Result |
|---|---|
| `cd backend; python -m pytest -q` | 27 passed; one Starlette/httpx deprecation warning |
| `cd backend; python -m ruff check app tests scripts` | Passed |
| `npm test -- --runInBand` | 6 passed across 2 suites |
| `npx tsc --noEmit` | Passed |
| `npx expo lint` | 0 errors; 25 warnings |
| `npx expo install --check` | Dependencies up to date |
| `npx expo-doctor` | 20/20 checks passed |
| `npx expo export --platform web` | Passed |
| Grade 6 / Grade 9 / Form 4 isolated API journeys | Passed; 100% synthetic answer runs |
| Auth and curriculum isolation | Missing bearer token denied (401); cross-level lesson denied (404) |
| Browser lesson journey and refresh | Passed with synthetic account after route/auth-hydration fix |
| Active DB and timestamped backup | Integrity `ok`; zero FK violations; learner-table rows match |
| `npm audit --omit=dev` | 14 advisories: 3 high, 11 low |
| Native iOS/Android builds or physical device | Not run |
| Public deployment | Not performed |

Expo lint warnings are existing style/import warnings; no lint errors were reported.
The backend test warning concerns the Starlette/httpx TestClient deprecation and is not a
test failure.

## Remaining release blockers

1. The Phase Five educational findings remain open: 45 lessons without objectives, four
   without explanation sections, 80 without lesson-level source locators, and 201
   short-answer questions without feedback. No expert review of the full catalog was
   completed in Phase Six.
2. Five source-register entries remain restricted and 42 remain unverified. No written
   permission or legal reuse clearance was obtained.
3. Child-data safeguards and decisions remain incomplete: privacy/consent/guardian
   requirements, deletion, retention, support, and leaderboard policy need specialist
   review and implementation.
4. Three high npm audit findings remain in the Expo CLI dependency chain. Do not apply
   the incompatible automatic Expo downgrade.
5. Production HTTPS/API hosting, durable hosted database, monitoring, rate limits,
   scheduled backups, operational ownership, rollback, and incident response remain
   unverified.
6. Native targets and a device-level journey were not validated.

Local test success does not establish educational correctness, licensing permission,
official KICD alignment, privacy/legal compliance, or production readiness. Keep the
external beta closed until each blocker has documented closure evidence and approval.
