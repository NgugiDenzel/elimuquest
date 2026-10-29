# Phase Five Beta Readiness Decision

**Decision: NOT READY for controlled beta.**  
**Deployment authorization: None. No deployment was performed.**

## Basis

The app's automated backend/frontend tests, TypeScript check, Ruff, Expo web export,
database integrity, importer dry-runs, and isolated SQLite restore passed. Those checks do
not establish educational correctness, source rights, privacy compliance, operational
readiness, or safe external learner access.

## Blockers to external learners

| Priority | Blocker | Current evidence | Closure evidence required |
|---|---|---|---|
| High | Dependency advisories and SDK compatibility | `npm audit --omit=dev` reports 5 high, 7 moderate, 7 low. Expo is 58.0.17 while direct `expo-constants` is 17.0.8 and Expo Router is 4.0.22; `expo install --check` was blocked by `ECONNRESET`. | Verify supported versions from SDK 58 documentation, review advisory reachability, then upgrade within the SDK matrix; rerun audit, Expo checks, web and native builds. |
| High | Educational accuracy and feedback | 124 published lessons; all need independent accuracy/level/language review. 45 lack objectives. 201 short-answer questions lack explanations. | Signed subject-expert review and verified corrections/feedback for each published lesson/question in scope. |
| High | Source rights and attribution | Source register has 5 restricted and 42 unverified entries; no source is marked verified for intended reuse. | Rights review; obtain written permissions or remove/rework reliance on restricted/unverified material before external use. |
| High | Learner privacy and child-data obligations | Personal profiles and learning histories are stored; leaderboard shows first names and XP. No in-app privacy notice, terms, or account-deletion flow was found. | Specialist review of consent, data minimization, retention, deletion, access controls, and parent/guardian obligations; implement required notices and flows. |
| High | Production operations | No production URL, TLS endpoint, hosted database, monitoring, error tracking, scheduled backups, rate limiting, or rehearsed operational rollback was verified. | Configure and test a secure environment, persistent data storage, HTTPS, exact CORS origins, rate limits, monitoring, backup schedule, and recovery procedure. |
| Medium | Learner workflow verification | Current browser opens the welcome screen; authenticated lesson access was not repeated in this audit. Historical reports contain representative checks. | Repeat full learner-role login → curriculum → lesson → answer → progress journey on deployed-like web and a supported native target. |
| Medium | Unsupported demo records | Three `LEGACY/Legacy` demo lessons are flagged published without reviewer metadata; that catalog is not a supported learner curriculum selection. | Decide disposition, correct metadata, and review/publish or archive using the authorized workflow. |
| Medium | Tooling verification | Expo SDK compatibility check failed with `ECONNRESET`; Docker was unavailable; Python advisory scanner is not installed. | Re-run in a networked build environment and verify Docker Compose and dependency state. |

## Release conditions

Do not invite external learners until the High blockers above have documented closure
evidence. Before a limited beta, also:

1. Confirm the supported grade/form scope and curriculum source versions with curriculum
   specialists; keep CBC/CBE and 8-4-4 distinct.
2. Review all source-license terms per specific book, version, page, image, and use.
3. Resolve npm advisories without unsafe broad upgrades; preserve the Expo SDK 58 compatible
   dependency set and validate both web and native targets.
4. Configure production with a unique JWT secret, explicit durable `DATABASE_URL`, exact
   HTTPS web origins, secure API URL, least-privilege access, and no public database port.
5. Verify learner privacy, consent, retention, account lifecycle, and incident response.
6. Re-test backup/restore and the authenticated learner journey against the intended beta
   environment with synthetic or authorized test data.
7. Establish support ownership, monitored error reporting, backup cadence, and rollback
   criteria before any deployment decision.

Passing the current test suite is necessary but does not demonstrate official curriculum
alignment, copyright clearance, legal compliance, or readiness for public deployment.
