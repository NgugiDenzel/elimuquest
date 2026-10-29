# Phase Five — Content Quality and Production Readiness Audit

**Audit date:** 2026-10-29  
**Decision:** **NOT READY for controlled beta**  
**Database writes:** None. The active database and learner records were not modified.

## Executive summary

The active database contains 17 subjects, 77 topics, 125 lessons (124 published), and
449 questions. There are 13 subject/curriculum/level combinations in the learner catalog
and four `LEGACY/Legacy` demonstration subjects that are not supported learner selections.
Legacy Form 4 remains separate from CBC/CBE grades.

All 125 lesson records and all 449 questions were checked for database relationships,
publication state, required fields, source/reviewer metadata, question structure, key-option
consistency, and exact normalized prompt duplicates. This is a structural and provenance
audit, **not** an independent subject-expert review of every explanation, distractor, or
answer. Accuracy and language remain unverified for the full published catalog.

The audit found material review gaps: 45 lessons have no recorded learning objectives,
four lessons have no explanation sections (three published demo records under an unsupported
curriculum label and the existing blocked Biology draft), 80 lesson records have no
lesson-level source locator, three published demo lessons lack reviewer metadata, and 201
short-answer questions have no explanatory feedback. No lessons are missing questions,
no topics are empty, and there are no duplicate lesson slugs or foreign-key violations.

Nine numerical answers in Grade 6 Mathematics Data Handling and legacy Form 4 Statistics II
were recalculated from the lesson datasets. These sampled values are consistent. This spot
check is not evidence that the remaining questions are accurate.

The previous API connection failure is documented as connection refusal while the backend
was not listening on port 8000. The backend is running and healthy in this audit. The
AuthProvider effect lint error was fixed and regression-tested. Production dependency
scanning still reports 5 high and 7 moderate advisories, and source licensing, learner
privacy, external deployment, and full educational review remain unresolved.

## Baseline and comparison

| Metric | Previously reported | Verified before audit | After audit |
|---|---:|---:|---:|
| Subjects | 17 | 17 | 17 |
| Topics | 77 | 77 | 77 |
| Lessons | 125 | 125 | 125 |
| Published lessons | 124 | 124 | 124 |
| Draft lessons | 1 | 1 | 1 |
| Questions | 449 | 449 | 449 |
| Archived / in-review / approved lessons | Not stated | 0 / 0 / 0 | 0 / 0 / 0 |

The active database path is `backend/elimuquest.db` when the backend is started from
`backend/`, consistent with the documented local command. No lesson, question, or learner
record was changed during this audit; before/after counts and learner-data hashes match.

## Scope and method

- Read the live SQLite database through a read-only connection and checked SQLite integrity,
  foreign keys, relationship counts, publication fields, metadata, question options and
  duplicate prompts.
- Created the Phase Five CSVs with the read-only exporter
  `backend/scripts/export_phase_five_audit.py`. It refuses to read a missing database and
  stops if SQLite integrity is not `ok`.
- Dry-ran the existing importer without `--apply` against the expansion, Mathematics, and
  Grade 6 book packages. These checks did not write to the active database.
- Reviewed current configuration, route authorization, answer scoring, frontend API error
  handling, package manifests, source register, startup documentation, and tests.
- Ran the available backend/frontend tests, Ruff, TypeScript, Expo lint, and web export.
- Checked a small number of mathematical answers directly. No full factual, language, or
  curriculum-alignment review by a qualified subject expert was performed.

The lesson, question, curriculum, and provenance records are in:

- [PHASE_FIVE_CONTENT_AUDIT.csv](./PHASE_FIVE_CONTENT_AUDIT.csv) — 125 lesson rows.
- [PHASE_FIVE_QUESTION_AUDIT.csv](./PHASE_FIVE_QUESTION_AUDIT.csv) — 449 question rows.
- [PHASE_FIVE_CURRICULUM_COVERAGE.csv](./PHASE_FIVE_CURRICULUM_COVERAGE.csv) — 77 topic
  rows.
- [PHASE_FIVE_SOURCE_AND_LICENSING_REGISTER.csv](./PHASE_FIVE_SOURCE_AND_LICENSING_REGISTER.csv)
  — 57 source/provenance rows.

## Verified curriculum inventory

| Curriculum / level | Subjects | Topics | Lessons | Published | Draft | Questions |
|---|---:|---:|---:|---:|---:|---:|
| 8-4-4 Form 4 | 5 | 24 | 42 | 42 | 0 | 146 |
| CBC/CBE Grade 6 | 4 | 19 | 37 | 37 | 0 | 140 |
| CBC/CBE Grade 9 | 4 | 30 | 42 | 42 | 0 | 158 |
| `LEGACY/Legacy` demo catalog | 4 | 4 | 4 | 3 | 1 | 5 |
| **Total** | **17** | **77** | **125** | **124** | **1** | **449** |

The catalog supports only the listed Grade 6, Grade 9, and Form 4 offerings. CBC/CBE
Grades 4–5, 7–8, and Senior School Grades 10–12 are not learner-supported in the current
catalog. The four `LEGACY/Legacy` demo subjects are not equivalent to 8-4-4 Forms 1–4 and
are not valid learner curriculum selections.

Per supported subject and level:

| Curriculum / level | Subject | Topics | Lessons / published | Questions |
|---|---|---:|---:|---:|
| 8-4-4 Form 4 | Chemistry | 3 | 8 / 8 | 24 |
| 8-4-4 Form 4 | English | 4 | 8 / 8 | 24 |
| 8-4-4 Form 4 | Kiswahili | 4 | 8 / 8 | 24 |
| 8-4-4 Form 4 | Mathematics | 10 | 10 / 10 | 50 |
| 8-4-4 Form 4 | Physics | 3 | 8 / 8 | 24 |
| CBC/CBE Grade 6 | English | 3 | 8 / 8 | 24 |
| CBC/CBE Grade 6 | Kiswahili | 4 | 8 / 8 | 24 |
| CBC/CBE Grade 6 | Mathematics | 9 | 13 / 13 | 68 |
| CBC/CBE Grade 6 | Science & Technology | 3 | 8 / 8 | 24 |
| CBC/CBE Grade 9 | English | 4 | 8 / 8 | 24 |
| CBC/CBE Grade 9 | Integrated Science | 4 | 8 / 8 | 24 |
| CBC/CBE Grade 9 | Kiswahili | 4 | 8 / 8 | 24 |
| CBC/CBE Grade 9 | Mathematics | 18 | 18 / 18 | 86 |

All 77 existing topics have at least one lesson. That count does not establish that the
topic set is complete: an authoritative, versioned syllabus scope was not audited for
every subject and level. The coverage assessment is therefore **provisional** and no
official curriculum completeness or KICD approval is claimed.

## Content and assessment findings

### Lesson records

- 124 of 125 lessons are published; the existing Biology demo remains draft and blocked.
- 45 records have no learning objectives. This includes Mathematics lessons whose
  structured explanation content exists, as well as demo records.
- Four records have no explanation sections. Three are legacy demonstration lessons that
  are marked published but sit under unsupported `LEGACY/Legacy`; the fourth is the
  unpublished `cell-structure` draft.
- 80 records have neither a lesson-level `source_id` nor `source_reference`. This does not
  prove that the content was copied, but it prevents direct source traceability.
- Three published `LEGACY/Legacy` demos have no reviewer/review timestamp. Four records
  have no author value.
- 41 Mathematics records have an empty legacy `content` field while holding structured
  explanation sections; those were not treated as empty lessons solely because the legacy
  field is unused.
- The database has zero lessons without questions, zero topics without lessons, zero
  publication-flag/status mismatches, and zero duplicate lesson slugs.

The lesson audit CSV assigns severity only to observable structural/provenance findings.
It records 120 Medium, one Low, and four “Not assessed” lesson rows. These values do not
represent a full educational-accuracy severity rating.

### Questions

- All 449 prompts and answer keys are present.
- All 248 multiple-choice keys match one of the recorded options structurally; correctness
  and distractor uniqueness/quality were not independently established by this check.
- All 201 short-answer questions lack explanatory feedback. Their answer keys are present,
  but numerical or semantic correctness has not been exhaustively recalculated.
- One exact normalized prompt, “Find the mode.”, appears in Grade 6 Data Handling and Form 4
  Statistics II. Each lesson supplies its own dataset, and the corresponding answers (4 and
  6) match those datasets. The repeated prompt is recorded for editorial review, not
  classified as a demonstrated answer-key error.
- The question audit contains 201 Medium rows for missing feedback and 248
  “Not assessed” rows. No Critical or High assessment error was established by structural
  checks; that is not proof that none exists.

The scoring implementation and tests establish these behaviors: multiple-choice answers
are case-insensitive exact matches; short answers normalize selected numeric and text
formats; one answer per question is accepted; malformed/unknown inputs are rejected;
incomplete sessions cannot be completed; duplicate completion does not award XP twice.
The current reward formula remains 10 XP plus 5 XP per correct answer. No scoring semantics
were changed.

## Sources, licensing, and curriculum alignment

The expanded source register has 57 entries: 5 are marked **Restricted — permission or
conditions required**, 42 **Unverified**, and 10 **Original content — provenance
documented**. No third-party source is marked “Verified for intended use.”

- The existing register records OpenStax Biology 2e and University Physics Volume 1 as
  CC BY-NC-SA 4.0 and notes OpenStax restrictions for generative-AI offerings without prior
  written permission. Those references are not treated as reuse clearance. The Grade 6
  Biology-sourced material remains a public-release review item.
- Chemistry 2e and University Physics Volumes 2–3 license/AI-offering terms were not
  independently established in the accessed pages and remain **Unverified**.
- Purdue OWL entries are reference-only; a copyright notice is not permission to reproduce.
- The Form 4 Mathematics PDF's publisher and reuse rights remain unverified.
- NIDDK and multiple syllabus/source references have no verified reuse clearance.
- New supplementary content is not represented as official KICD curriculum content.

No material was deleted or unpublished during this audit. Any future publication change
must use the authenticated review workflow and have a source-specific rationale.

## Technical, privacy, and recovery findings

- The frontend’s current request layer distinguishes transport failure, timeout, HTTP/API
  status, and malformed JSON. Existing client tests cover connection refusal, HTTP 401,
  timeout, and malformed successful responses.
- The previous exact “could not reach” incident was recorded as `ERR_CONNECTION_REFUSED`
  while port 8000 had no backend listener. Starting Uvicorn resolved that incident. In this
  audit, the backend on port 8000 and web app on 8081 were reachable; the old failure was
  not reproduced as a current outage.
- Current live `/health` and `/readiness` returned HTTP 200. CORS preflight for
  `http://localhost:8081` returned 200 with that exact allowed origin.
- The browser page was at the public welcome screen. An authenticated learner lesson
  journey was not repeated during this audit; earlier regression documentation contains
  representative UI/API checks.
- Password hashes use Argon2id and bearer tokens use signed, expiring JWTs. Registration
  creates student roles; administrator access is role-checked. Native token storage uses
  SecureStore; web token storage uses AsyncStorage.
- The platform stores names, email addresses, curriculum profile, lesson sessions,
  answers, progress, XP, and achievements. The leaderboard displays first names and XP.
  No privacy notice, terms, or account-deletion flow was found in the app. Specialist
  review of child-data, retention, consent, and deletion obligations is required; this
  audit makes no legal-compliance claim.
- The Docker image now defaults to production configuration and rejects the development
  JWT secret, default SQLite URL, or non-HTTPS/local CORS origins. The local Postgres
  Compose password is now required from an ignored environment file and its port is
  loopback-only. Docker was unavailable, so the Compose file was not executed or built.
- `npm audit --omit=dev` reported 19 production-tree advisories: 5 high, 7 moderate, and
  7 low. The proposed Expo fix would downgrade across SDK major versions, while other
  suggested fixes include major package updates. No automated dependency changes were
  applied. Reachability of each advisory in the shipped application has not been
  established.
- `npx expo install --check` could not complete because the registry connection reset.
  `pip-audit` is not installed. Native iOS/Android builds and hosted deployment were not
  tested.
- The manifest pins Expo 58 with direct `expo-constants` 17 and Expo Router 4; the lock/tree
  also contains Expo 58-era transitive packages. Compatibility is not asserted: the SDK
  check could not reach the registry, and native builds were not run.

## Test results

| Check | Result |
|---|---|
| `cd backend; python -m pytest -q` | 27 passed; one Starlette/httpx deprecation warning |
| `cd backend; python -m ruff check app tests scripts` | Passed |
| `npm test -- --runInBand` | 6 passed |
| `npx tsc --noEmit` | Passed |
| `npx expo lint` | 0 errors; 27 existing warnings |
| `npx expo export --platform web` | Passed |
| Importer dry-run: 26 coverage packages | 0 created, 58 unchanged, 0 rejected |
| Importer dry-run: 36 Mathematics packages | 0 created, 36 unchanged, 0 rejected |
| Importer dry-run: Grade 6 whole-number package | 0 created, 5 unchanged |
| Active DB and backup integrity / FK checks | `ok`; zero FK violations |
| Isolated restore test | Passed; restored copy had expected counts and zero FK violations |
| Production npm advisory check | 5 high, 7 moderate, 7 low; remediation outstanding |

## Limitations and prioritized remediation

1. **High — Dependency security:** determine affected runtime/build reachability and upgrade
   within the Expo SDK 58 compatibility set; rerun audit, Expo checks, web and native builds.
2. **High — Content review:** engage subject experts to verify all published lessons and
   keys; add explanations to the 201 short-answer questions and objectives where needed.
3. **High — Licensing:** resolve the five restricted entries and 42 unverified source
   records; secure permission or replace/rework affected references before external use.
4. **High — Learner privacy:** obtain specialist child-data review and provide privacy,
   retention, consent, and account lifecycle mechanisms before inviting external learners.
5. **High — Operations:** configure an HTTPS API, exact CORS allowlist, persistent storage,
   rate limits, monitored logs, backup schedule, and rehearsed recovery.
6. **Medium — Curriculum mapping:** verify syllabus version and coverage per subject/topic;
   review unsupported `LEGACY/Legacy` published demo records through the admin workflow.
7. **Medium — UX:** verify the authenticated learner journey on web and at least one
   supported native target; add visible educational feedback for short-answer questions.

## Beta readiness

**NOT READY.** Passing application tests is not enough to clear the unresolved dependency
advisories, licensing, content accuracy, child-data/privacy, persistence, monitoring, and
learner-journey blockers. This is an audit decision only, not authorization to deploy.
