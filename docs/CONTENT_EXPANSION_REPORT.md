# Content expansion report — 2026-10-29

## Initial state and audit

The active database is `backend/elimuquest.db`. Its verified pre-import state was:

| Entity | Before |
|---|---:|
| Subjects | 17 |
| Topics | 41 |
| Lessons | 45 |
| Questions | 209 |
| Published lessons | 44 |
| Draft lessons | 1 |
| Users | 2 |
| Answer attempts | 37 |
| Lesson progress rows | 10 |
| Lesson sessions | 26 |
| XP transactions | 14 |
| Achievements | 1 |
| User achievements | 2 |
| Daily activity rows | 3 |

The single baseline draft was the legacy demo Biology lesson. Existing learner-facing mathematics content was in CBC/CBE Grade 6 and Grade 9 and legacy 8-4-4 Form 4. Grade 6 English and Science & Technology were seeded in the supported curriculum catalog but had no topics or lessons. Other empty supported selections included Grade 6 Kiswahili, Grade 9 English, Integrated Science and Kiswahili, and Form 4 English, Chemistry, Kiswahili and Physics. The `LEGACY/Legacy` demo subjects are not equivalent to supported Form 4 curriculum entries.

The current catalog supports CBC/CBE Grade 6, CBC/CBE Grade 9, and legacy 8-4-4 Form 4. It does not expose CBC/CBE Grades 4–5 or Senior School Grades 10–12. These were not invented or added.

Historical documents incorrectly described the Grade 6 Whole Numbers material as draft and described the imported mathematics lessons as drafts. The active database showed all 44 non-demo baseline lessons, including the five Whole Numbers pupil-book lessons, as published. The source register has been corrected to the actual database state; the original source access dates for older user-provided packages remain unknown.

## Batch selection and content created

Grade 6 English and Grade 6 Science & Technology were selected because the actual supported catalog had zero topics and lessons for both, while the app already supports their Grade 6 subject mappings. The work deliberately adds coherent topics and lessons rather than placeholder catalog entries.

| Curriculum / level | Subject | Topic | Lessons | Questions | Imported state |
|---|---|---|---:|---:|---|
| CBC/CBE Grade 6 | English | Reading and Vocabulary | 3 | 9 | Published |
| CBC/CBE Grade 6 | Science & Technology | Plants and Habitats | 3 | 9 | Published |

Lessons created:

- English: Reading for main ideas; Using context clues; Punctuation and sentence types.
- Science & Technology: Plant parts and their functions; Food chains and ecosystems; Habitats and adaptation.

The packages include learning objectives, prerequisites, explanatory sections, worked examples, answer explanations, and foundational/intermediate multiple-choice questions. Answer keys were checked against the explanations. The punctuation item was rewritten to avoid a style-dependent Oxford-comma ambiguity. A false camel-water-storage explanation was removed and replaced with a source-supported example about deep roots in dry areas.

## Sources and curriculum verification

- OpenStax *Biology 2e*, sections 30.1–30.3 and 46.1, was accessed on 2026-10-29 for plant structures/functions, root adaptations, ecosystem/habitat concepts, and food chains. Lesson text is original summary; no source passages were copied. The source register records the publisher license and exact URLs.
- Purdue OWL at Purdue University, “Punctuation,” was accessed on 2026-10-29 for the punctuation lesson. Explanations are original paraphrases; no source text was reproduced.
- The reading comprehension and context-clue lessons are original ElimuQuest material and do not claim a specific external source.
- The content is mapped to the application's Grade 6 English and Science subject selections, but official KICD curriculum alignment has not been verified. No official strand, page, or approval claim is made.
- The supplied 124-page `MATHS FORM 4 NOTES.pdf` was accessible and inspected. It contains legacy Form 4 mathematics material, including matrices and transformations, Statistics II, three-dimensional geometry, Trigonometry III, longitudes and latitudes, linear programming, loci, differentiation, integration, and area approximation. Its publisher/reuse license was not verified. No new Form 4 material was created from it in this batch.

## Import and publication outcome

- A fresh SQLite backup was created before the import at `backend/backups/elimuquest-phase3-20261029-112235.db`. It was non-empty and passed `PRAGMA integrity_check`.
- Both packages passed the existing Pydantic/importer dry-run: 3 lessons eligible per package, no rejected records.
- The existing `import_content` importer was used in a single database transaction. It created 2 topics, 6 lessons, and 18 questions. Existing content was not overwritten.
- A second dry-run reported 0 created and 3 unchanged for each package. No duplicate lesson slugs or question IDs were found.
- The importer correctly left all new lessons as `draft` (`published=false`). No publication state was modified outside the authorized review workflow.
- An authorized admin account submitted the six lessons for review, approved them, and published them through the existing admin interface on 2026-10-29. Each lesson records the reviewer and publication timestamp. No database status columns were changed directly.
- Final state: 17 subjects, 43 topics, 51 lessons, 227 questions; 50 published lessons and one draft lesson. The remaining draft is the pre-existing demo Biology lesson.
- The new content is returned by authenticated Grade 6 learner interfaces. The English subject reports three published lessons and its learning path lists all three. The first English lesson opened with its explanation and quiz question/options. The Science & Technology path lists all three lessons and its first lesson opened with its quiz question/options.

## Database integrity and learner data

| Entity | Before | After | Change |
|---|---:|---:|---:|
| Subjects | 17 | 17 | 0 |
| Topics | 41 | 43 | +2 |
| Lessons | 45 | 51 | +6 |
| Questions | 209 | 227 | +18 |
| Users | 2 | 2 | 0 |
| Answer attempts | 37 | 37 | 0 |
| Lesson progress rows | 10 | 10 | 0 |
| Lesson sessions | 26 | 26 | 0 |
| XP transactions | 14 | 14 | 0 |
| Achievements | 1 | 1 | 0 |
| User achievements | 2 | 2 | 0 |
| Daily activity rows | 3 | 3 | 0 |

The database and backup both passed SQLite integrity checks. Comparisons of all rows in the learner/account/history tables above were identical between the backup and active database.

## Remaining gaps

Grade 6 Kiswahili, Grade 9 English, Integrated Science and Kiswahili, and Form 4 English, Chemistry, Kiswahili, and Physics remain without supported instructional content. Existing mathematics coverage remains partial rather than comprehensive. Official alignment of the new supplementary lessons remains unverified. Public deployment remains out of scope.

## Phase Four expansion — 2026-10-29

The Phase Three totals above are historical. The current active database was rechecked immediately before the Phase Four import: 17 subjects, 43 topics, 51 lessons, 227 questions, 50 published lessons and one draft legacy Biology demo. The verified pre-import backup is `backend/backups/elimuquest-phase4-20261029-122116.db` (376,832 bytes; SQLite integrity check `ok`; contained 43 topics, 51 lessons and 227 questions). It also recorded 2 users, 37 answer attempts, 10 lesson-progress rows, 28 lesson sessions, 14 XP transactions, 1 achievement, 2 user achievements and 3 daily activity rows.

### Selected coverage and work performed

The batch targeted all eight supported subject/level pairs that had zero instructional lessons. This was the highest-value selection because these existing catalog entries were otherwise empty. The app currently supports CBC/CBE Grade 6, CBC/CBE Grade 9 and legacy 8-4-4 Form 4; no Grade 10 content was mixed with Form 4.

| Curriculum / level | Subject | Topic | Lessons | Questions |
|---|---|---|---:|---:|
| CBC/CBE Grade 6 | Kiswahili | Lugha: Nomino, Vivumishi na Vitenzi | 2 | 6 |
| CBC/CBE Grade 9 | English | Reading and Writing | 2 | 6 |
| CBC/CBE Grade 9 | Kiswahili | Kusoma na Kuandika | 2 | 6 |
| CBC/CBE Grade 9 | Integrated Science | Energy and Ecosystem Interactions | 2 | 6 |
| 8-4-4 Form 4 | English | Communication Skills | 2 | 6 |
| 8-4-4 Form 4 | Kiswahili | Uandishi na Nyakati za Vitenzi | 2 | 6 |
| 8-4-4 Form 4 | Chemistry | Equations and Acids | 2 | 6 |
| 8-4-4 Form 4 | Physics | Motion and Electricity | 2 | 6 |

These are AI-assisted original starter lessons, not comprehensive course coverage. Package files contain the lesson explanations, learning objectives, worked examples and multiple-choice questions with answer explanations. The packages make no claim of official KICD alignment and do not cite unverified sources. Their source and license status is recorded in `docs/EDUCATIONAL_SOURCE_REGISTER.csv`.

### Import, review and publication

- All eight packages passed Pydantic/importer dry-run validation: 16 new lessons and 48 questions eligible, no package rejected. All 48 multiple-choice keys matched an option and included explanations.
- A single `SessionLocal.begin()` transaction imported 8 topics, 16 lessons and 48 questions; the importer created only drafts. Repeat dry-runs returned `created=0`, `unchanged=2` for every package.
- The authenticated admin preview identified 16 eligible records and one blocked pre-existing demo (`cell-structure`, missing required explanation sections). The authenticated bulk publication workflow published all 16 new lessons. No lesson or question was inserted twice.
- The existing bulk endpoint initially moved the blocked demo from draft to in-review before rejecting it. That defect was fixed by validating before any transition; a regression test was added, and the demo was returned through the authorized status API to its original `draft`/unpublished state.
- Final state: 17 subjects, 51 topics, 67 lessons, 275 questions; 66 published lessons and one draft legacy demo. No in-review, approved, or archived lessons remain. The sole draft is intentionally blocked and is not a supported learner curriculum lesson.
- The live authenticated Grade 6 learner-facing API lists Kiswahili and returns its two lessons; the existing account used has the admin role and a Grade 6 curriculum profile, so this was not represented as a student-role login test. A direct lesson request without authentication returns HTTP 401. Grade 9 and Form 4 curriculum paths were verified from database publication state and the API's curriculum-scoped regression tests rather than by changing user profiles.

### Data preservation, sources and release note

The active database and backup both return `PRAGMA integrity_check = ok`. Before/after row counts and stable table hashes match for users, attempts, progress, sessions, XP, achievements, user achievements and daily activity. Counts remain 2, 37, 10, 28, 14, 1, 2 and 3 respectively; this import/publication did not award learner XP or create attempts/progress.

**Public-release blocker:** the earlier Grade 6 Science lessons cite OpenStax Biology 2e. The source register previously incorrectly called its license CC BY 4.0; it is corrected to CC BY-NC-SA 4.0 and notes the additional OpenStax restriction on use in AI offerings absent written permission. Obtain permission or replace/remove the affected sourced content before public launch. No production deployment was performed. The user-provided Form Four mathematics PDF's reuse license also remains unverified.

The remaining curriculum gap is depth rather than empty supported subjects: all supported catalog subject/level pairs now have at least some lessons, but each new two-lesson starter batch and the existing mathematics courses need subject-expert review, curriculum mapping and further topic-by-topic expansion.

## Curriculum coverage audit and expansion — 2026-10-29

### Diagnosis and verified baseline

The active catalog contains 13 learner-supported subject/curriculum/level combinations: CBC/CBE Grades 6 and 9, and legacy 8-4-4 Form 4. The four `LEGACY/Legacy` demonstration subjects are not supported learner curricula and were kept separate. The catalog does not support CBC/CBE Grades 4–5 or Senior School Grades 10–12; no such entries were added. Legacy Form 4 was never treated as Grade 10.

Immediately before this batch, the active database contained 17 subjects, 51 topics, 67 lessons, 66 published lessons and 275 questions. Ten supported combinations were markedly under-populated:

| Curriculum / level | Subject | Topics | Lessons | Published | Questions |
|---|---|---:|---:|---:|---:|
| 8-4-4 Form 4 | Chemistry | 1 | 2 | 2 | 6 |
| 8-4-4 Form 4 | English | 1 | 2 | 2 | 6 |
| 8-4-4 Form 4 | Kiswahili | 1 | 2 | 2 | 6 |
| 8-4-4 Form 4 | Physics | 1 | 2 | 2 | 6 |
| CBC/CBE Grade 6 | English | 1 | 3 | 3 | 9 |
| CBC/CBE Grade 6 | Kiswahili | 1 | 2 | 2 | 6 |
| CBC/CBE Grade 6 | Science & Technology | 1 | 3 | 3 | 9 |
| CBC/CBE Grade 9 | English | 1 | 2 | 2 | 6 |
| CBC/CBE Grade 9 | Integrated Science | 1 | 2 | 2 | 6 |
| CBC/CBE Grade 9 | Kiswahili | 1 | 2 | 2 | 6 |

The three Mathematics offerings had 10, 13 and 18 lessons respectively and were not part of this first content batch. No supported combination had zero lessons at this baseline; the preceding Phase Four work had already filled those empty selections.

The verified cause of the recurring two-lesson pattern was package-authoring scope: earlier starter packages were authored with two lessons each. It was not an importer limit. The importer validates and processes every lesson in each package, remains idempotent by lesson content hash, and this batch's directory import accepted packages containing both two and three lessons. The learner API filters by the learner's curriculum and published status but does not cap or paginate the path; the app renders every lesson returned. The five-lesson learner-path regression test also passes.

### Coverage target and selection rationale

The proposed initial planning floor is eight substantial lessons distributed across at least three topics for each under-populated supported subject/level. The target is deliberately higher for broader or more technical subjects: 10–12 lessons for the Science offerings and Form 4 language offerings, and 12–20 for the Mathematics offerings, with corresponding topic targets recorded in the coverage matrix. These are provisional planning targets, not claims that an official course or syllabus is complete. All ten combinations at or below three lessons were selected because they had the greatest immediate learner-content deficit and were already supported by the catalog and interface.

### Content created and imported

Twenty-six packages were validated and imported atomically through the existing content importer. They added **26 topics, 58 original AI-assisted lessons and 174 questions**:

| Curriculum / level | Subject | New topics | New lessons | New questions |
|---|---|---:|---:|---:|
| 8-4-4 Form 4 | English | 3 | 6 | 18 |
| 8-4-4 Form 4 | Kiswahili | 3 | 6 | 18 |
| 8-4-4 Form 4 | Chemistry | 2 | 6 | 18 |
| 8-4-4 Form 4 | Physics | 2 | 6 | 18 |
| CBC/CBE Grade 6 | English | 2 | 5 | 15 |
| CBC/CBE Grade 6 | Kiswahili | 3 | 6 | 18 |
| CBC/CBE Grade 6 | Science & Technology | 2 | 5 | 15 |
| CBC/CBE Grade 9 | English | 3 | 6 | 18 |
| CBC/CBE Grade 9 | Integrated Science | 3 | 6 | 18 |
| CBC/CBE Grade 9 | Kiswahili | 3 | 6 | 18 |

Lessons include learning objectives, explanations, examples where useful, concise recaps, and three multiple-choice questions with answer options and explanatory feedback. Content was manually reviewed for factual consistency and numerical keys recalculated. The package metadata marks content as AI-assisted and leaves official source IDs and lesson source references null where no specific curriculum document or source text was used; no unverified official citation was invented.

### Research, attribution and verification status

The educational source register now records source titles, publishers, exact URLs, sections, access dates and the reuse information found. OpenStax Chemistry 2e and University Physics Volumes 1–3 were consulted only for selected factual cross-checks after drafting. No textbook wording, illustrations or assessment items were copied into the packages. The accessed University Physics Volume 1 introduction states a CC BY-NC-SA 4.0 license and requires prior written permission for use in generative-AI offerings; reuse terms for Chemistry 2e and Volumes 2–3 were not independently surfaced in the accessed pages. None of these references is treated as license clearance or incorporated package content. Purdue OWL and NIDDK were also consulted as references; no text was reproduced. No official KICD curriculum document or expert endorsement was verified for this batch. The content is supplementary, official alignment remains unverified, and every new subject/level awaits independent subject-expert review.

### Import, idempotency and publication

- The timestamped pre-import backup is `backend/backups/elimuquest-coverage-expansion-20261029-134721.db` (430,080 bytes); both the backup and active database passed `PRAGMA integrity_check`.
- The existing importer dry-run validated all 26 packages: 58 lessons and 174 questions eligible, no rejects. A single `SessionLocal.begin()` apply created 26 topics, 58 lessons and 174 questions as drafts.
- A repeat dry-run reported `created=0`, `unchanged=58`.
- The authenticated admin publication preview reported 58 eligible lessons and one blocked pre-existing Biology demo. The authenticated bulk workflow published all 58 eligible lessons. The blocked `cell-structure` record remained an unpublished draft because its explanation sections are missing.
- No publication columns were updated directly. The new lessons were all independently authored by the curriculum team, so the authenticated reviewer was distinct from their recorded author.

### Actual before/after totals and preservation

| Entity | Before | After | Change |
|---|---:|---:|---:|
| Subjects | 17 | 17 | 0 |
| Topics | 51 | 77 | +26 |
| Lessons | 67 | 125 | +58 |
| Published lessons | 66 | 124 | +58 |
| Questions | 275 | 449 | +174 |
| Draft lessons | 1 | 1 | 0 |

The remaining draft is the pre-existing blocked Biology demo. No lesson remains in `in_review`, `approved` or `archived`. There are no duplicate lesson slugs or question IDs, and the active database passes SQLite integrity checking.

Compared with the verified pre-import backup, full row hashes and counts match exactly for users (2), answer attempts (37), progress (10), lesson sessions (30), XP transactions (14), achievements (1), user achievements (2) and daily activity rows (3). The current verified snapshot had 30 sessions; an older report's 28-session count was stale by the time this batch's backup was taken. The learner login/profile used for testing was restored from the backup, and the one uncompleted session created by opening a lesson in the UI was removed after confirming it had no attempts. No answers, progress, XP or achievements were added.

### Learner experience and remaining gaps

With a real student-role account, the authenticated API returned eight lessons per tested subject path for Grade 6 English and Science & Technology, Grade 9 Integrated Science and Kiswahili, and Form 4 Chemistry and Physics; each opened lesson returned its three questions. A Grade 6 lesson request made while the same learner was set to another curriculum returned 404, confirming curriculum isolation. The browser UI was also logged in as that student: Grade 6 English displayed all eight lessons, opened a new lesson with its objectives, explanations, recap and quiz question/options; Grade 9 Integrated Science and Form 4 Chemistry subject and learning-path screens each displayed eight published lessons. The temporary test credential and curriculum profile were restored, and the learner record hashes match the backup.

The current matrix distinguishes planning-target gaps from completeness. Form 4 Chemistry and Physics, Grade 9 Integrated Science, the three existing Mathematics combinations, Form 4 English and Kiswahili, and Grade 6 Science & Technology remain below their working planning targets. Even where the starter target is met, coverage remains supplementary and partial—not a complete official curriculum. The four `LEGACY/Legacy` demo subjects remain outside the supported curriculum matrix and were not relabeled.

No public deployment was performed. The existing Grade 6 Biology-sourced material and any future use of OpenStax references in the AI offering still require the documented licensing review or replacement before public release.
