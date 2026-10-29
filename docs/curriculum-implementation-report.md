# Curriculum and frontend implementation report

Date: 2026-10-24
Mathematics draft integration update: 2026-10-24
Grade 6 Whole Numbers publication update: 2026-10-24

## Implemented

- Added explicit curriculum identity and level metadata to learners, subjects, topics and lessons. Registered CBC/CBE Grade 6, CBC/CBE Grade 9, and 8-4-4 Form 4 as distinct selections.
- Added the requested subject catalogues: Grade 6 Mathematics, English, Kiswahili, Science & Technology; Grade 9 Mathematics, English, Kiswahili, Integrated Science; Form 4 Mathematics, English, Kiswahili, Chemistry and Physics.
- Kept Grade 6/Grade 9 science as official learning areas; no Chemistry/Physics standalone subject or unsupported topic filters were added for those grades.
- Scoped subject lists/details, learning paths, lesson retrieval, current lesson, and subject mastery/accuracy to the learner's selected curriculum and level. XP and streak remain account-wide.
- Added a curriculum picker to the dashboard, explicit empty states where no reviewed lessons are published, structured objective/explanation/example rendering, and a protected admin review page.
- Added curriculum source/provenance, content version, objective, prerequisite, example, difficulty, author/reviewer timestamps, publication state, and AI-assisted flag fields. Old subjects migrate to `LEGACY` rather than being silently assigned to an unrelated curriculum.
- Added admin-only Draft → In review → Approved → Published → Archived transitions. Approval checks mapped source ID, a page/section locator, required lesson structure, answer/explanation consistency and a reviewer distinct from the author. Learner APIs require both the published flag and Published state.
- The admin review screen warns reviewers when a source is a provisional ElimuQuest draft or when the supplied book excerpt omits its answer key.
- Added a Pydantic JSON package contract and transactional importer. Dry-run is the default; `--apply` imports drafts; repeated identical packages are idempotent; mismatched slugs cannot overwrite existing content. Multiple-choice and short-answer grading are supported.
- Added the requested audit, source register, CSV coverage matrix, package schema/sample and this report.

## Mathematics draft integration

- Integrated all 36 lessons and 184 short-answer questions from the user-supplied *ElimuQuest Mathematics Curriculum Draft* v1. The supplied manuscript is the content source, not an official curriculum syllabus.
- Grade 6: Whole Numbers (p. 4); Multiplication and Division (pp. 4–5); Fractions (p. 5); Decimals and Percentages and Inequalities (p. 6); Measurement (pp. 6–7); Geometry (p. 7); Data Handling (pp. 7–8). Eight packages, 48 questions.
- Grade 9: Integers and Cubes and Cube Roots (p. 9); Indices and Logarithms and Compound Proportions and Rates of Work (p. 10); Matrices (pp. 10–11); Equation of a Straight Line and Linear Inequalities (p. 11); Area and Volume and Mass, Volume, Weight and Density (p. 12); Time, Distance and Speed (pp. 12–13); Money and Approximations and Errors (p. 13); Coordinates and Graphs (pp. 13–14); Scale Drawing and Similarity and Enlargement (p. 14); Trigonometry (pp. 14–15); Data Interpretation — Grouped Data and Probability (p. 15). Eighteen packages, 86 questions.
- Form 4: Matrices and Transformations (p. 16); Statistics II (pp. 16–17); Loci and Trigonometry III (p. 17); Three-Dimensional Geometry (pp. 17–18); Longitudes and Latitudes and Linear Programming (p. 18); Differentiation and Area Approximation (p. 19); Integration (pp. 19–20). Ten packages, 50 questions.
- Package page citations preserve traceability to the 21-page draft. They do not verify official learning outcomes or topic alignment. Grade 6 and Form 4 official Mathematics source research remains unresolved; the supplied draft also does not establish Grade 9 alignment to the revised KICD design.
- The manuscript does not provide a separate objective list, standalone worked-example records, or per-question explanations. Those were not invented. Its explanatory text is kept in lesson sections, and incorrect short answers receive the preserved answer key after submission. Short-answer comparison accepts normalized numeric formatting, whitespace, case, hyphen variants and final punctuation without changing the stored key.
- All 368 question-prompt and stored-answer strings were compared with extracted text from the supplied PDF; none were unmatched. This verifies transfer fidelity, not mathematical correctness.
- Packages are marked non-demo, not AI-generated, and import as draft/unpublished only. No qualified human reviewer has approved or published the production drafts.

## Grade 6 Whole Numbers pupil-book integration

- Integrated the supplied six-page *Grade 6 Mathematics: Pupil’s Book* excerpt as a separate, ordered five-lesson module under Grade 6 Mathematics, Strand 1: Numbers, Sub-strand 1.1: Whole Numbers.
- The five quizzes follow the book’s sequence: Place value and total value (2 questions); Reading and writing numbers in words (5); Ordering numbers (3); Rounding off to the nearest thousand (5); Squares and square roots (5). All 20 prompts are taken from practice questions 1–8; multipart questions are split into subparts to fit the existing quiz model.
- The package retains the source’s introductory harambee example, key inquiry question, explanations, worked examples 1–3, place-value table, diagram descriptions, glossary, number builders/square tiles group activity, “Talk about this” prompt, “Remember” summary, Kenyan currency context, and original practice-question wording. Text and line breaks are stored in the existing lesson explanation sections; no explanatory prose was generated.
- All six PDF pages were inspected. Page 5 says that answers will appear in the answer key at the end of Strand 1, but this supplied file ends at page 6 and contains no answer-key section. The 20 stored grading keys were independently calculated from the questions and taught methods; they are explicitly identified in each lesson’s source reference as calculated, not textbook answers. The review screen flags this limitation.
- Independently checked all 20 keys: Q1(a,b) twenty-three thousand, four hundred and fifty; sixty thousand and eight. Q2(a,b) 68,005; 90,412. Q3(a,b) “Hundred thousands; 600,000”; “Thousands; 2,000”. Q4 ascending: Ksh 4,999; Ksh 45,096; Ksh 45,609; Ksh 54,069. Q5(a–d) 34,000; 79,000; 97,000; 100,000. Q6(a–d) 81; 625; 13; 60. Q7 35 tiles. Q8(a–d) 97,530; 30,579; ninety-seven thousand, five hundred and thirty; 31,000. These are mathematical verification by this implementation, not human review or official KICD answer-key answers.
- Numeric short answers accept equivalent grouping/spacing (for example, `68005` for `68,005`) and reject malformed grouping. Written-number answers accept case, punctuation, spacing, and hyphen differences. Existing persisted lesson sessions, scoring, answer feedback, progress, and XP are reused. A completed lesson screen now offers an explicit “Try quiz again” action that starts a fresh attempt.
- The admin review screen now displays complete lesson explanation content, worked-example fields when present, all question choices, answers, citations and review-status disclosures. Admin listings follow topic/lesson ordering. The existing role-protected review/publication endpoints remain the only publication path.
- The import remains draft-only and idempotent. In the test database, the new end-to-end API test exercises all five quizzes, incorrect and correct marking, score/XP, saved attempts, progress after reauthentication, duplicate-completion protection, and retry behavior.

## Authorized publication and learner verification

- The existing five lessons and 20 questions were published in the local SQLite database using the signed-in admin interface and its existing transitions: Draft → In review → Approved → Published. No content was rewritten, reimported, or duplicated. All five rows have `published=true`, `content_status=published`, the authorized reviewer and publication timestamps. The source disclosure remains on every lesson.
- The signed-in browser showed Grade 6 Mathematics with five published lessons. The learning path displayed all five in the correct order, and each lesson opened through its normal learner route. The lesson text, number notation, superscripts and square-root symbols were present in the rendered screens.
- Browser quiz results: Place value 1/2 (50%, including a rejected answer and explanatory feedback); Reading and writing 5/5; Ordering 3/3; Rounding 5/5; Squares and square roots 5/5. A retry of Squares and square roots opened a fresh quiz session and completed at 5/5. XP was awarded under the existing scoring rule: 180 XP total across the six completed sessions. The subject page showed 100% mastery and five published lessons after navigation/refresh; SQLite retained five lesson-progress records and the completed answer attempts.
- The learner question screen did not show stored answer keys before submission. A wrong answer showed “Not quite” and its explanation; correct answers showed “That’s correct!”.
- The authorized admin interface was used to review and publish the module; the user explicitly reported personally reviewing the five lessons and questions. This does not establish formal teacher qualification or turn the independently calculated keys into official textbook answers. The excerpt’s referenced answer key is still missing.
- Browser/API tests used the local development admin account. The run left some incomplete sessions with no submitted answers and no XP while opening lessons/routes; they were preserved. No learner progress or XP was awarded for those sessions.

## Verification performed

- Pre-change baseline before this integration: 9 backend tests passed.
- Mathematics-manuscript baseline `python -m pytest -q`: 10 passed, with one existing Starlette/httpx deprecation warning.
- Final `python -m pytest -q`: 18 passed, with one existing Starlette/httpx deprecation warning.
- Final `python -m ruff check app tests alembic`: passed.
- Final `npm run typecheck`: passed.
- Final `npx expo export --platform web --output-dir <session-temp-dir>`: passed; export was written outside the project.
- Final `python -m alembic check`: no new upgrade operations detected; no schema migration was needed.
- The focused learner-journey/API test passes all five quizzes, answer/feedback checks, retry, score/XP calculations, persisted progress, and duplicate-completion protection. Review API tests verify admin-only access and draft-to-published transitions in the isolated test database; learner tests verify unpublished direct lesson retrieval is denied.
- SQLite importer dry-run before publication: `created=0`, `unchanged=5`, `status=draft`; no import was repeated or applied during publication. The five lessons and 20 questions remain exactly once in the local database, now published. Totals are 41 topics, 45 lessons, 209 questions; no migration ran.
- The authorized local admin account used the existing admin UI and API authorization workflow. Publication was limited to the five Grade 6 book lessons; the separate 36-manuscript lesson packages remain drafts.
- Browser verification was completed with the signed-in account. The backend is using local SQLite; PostgreSQL and native Android/iOS behavior remain unverified.
- The existing curriculum API tests cover subject lists, Grade 6/Grade 9 science naming, level isolation, invalid mapping rejection, review permissions, protected publication, and importer dry-run/idempotency.

## Curriculum sources researched and mapped

- The KICD Grade Nine Designs page lists English, Integrated Science, Kiswahili and Mathematics. The Integrated Science viewer identifies the Grade 9 Junior School Curriculum Design, first published 2024, ISBN 978-9914-52-946-3; its embedded filename is “Integrated Science Grade 9 - July 2024.pdf”. The same listing identifies the revised Grade 9 Mathematics PDF.
- The KICD Grade Six Designs page lists English, Kiswahili, Mathematics and Science and Technology.
- These page-level sources support the level/subject catalogue only. Topic sequences, strands, sub-strands and learning outcomes have not been mapped. The 8-4-4 Form 4 syllabuses and their edition/version have not yet been located or verified.

See [curriculum-source-register.md](./curriculum-source-register.md) and [curriculum-coverage-matrix.csv](./curriculum-coverage-matrix.csv) for citation state and coverage per subject.

## Content awaiting review

- Thirty-six Mathematics packages are awaiting a human subject-matter review and remain unpublished drafts. Ordinary learners cannot access them through learner APIs before the existing review and publication workflow is completed.
- Official curriculum outcomes, strands, sub-strands, and topic-sequence alignment have not been asserted from the ElimuQuest manuscript. The existing fictional demos remain Legacy/demo, and the sample package is intentionally rejected until its placeholder citations are replaced.
- The 36 user-manuscript Mathematics packages remain unpublished drafts awaiting qualified subject-matter review and official syllabus mapping. The user’s review and publication authorization apply to the five Grade 6 book lessons only.
- The Grade 6 book module is published in the local development database at the user’s explicit direction. Its marking keys remain independently calculated, not official textbook/KICD answers; the PDF does not expose a publisher or ISBN in its metadata, and no public URL was supplied.

## Known limitations and next steps

- Inspect the Grade 6 Science & Technology design and identify the exact edition/ISBN, then inspect the Grade 9 English/Kiswahili/Mathematics designs and extract relevant page-level references.
- Locate and verify the applicable Form 4 8-4-4 Mathematics, English, Kiswahili, Chemistry and Physics syllabuses and official topic sequences.
- After mapping, prepare original draft content, subject-matter review it, then exercise the publication path with one genuinely cited lesson before claiming a complete curriculum learner journey.
- The browser journey covered the local web app only. A separate student-role browser session and native Android/iOS journey were not run. Backend tests cover unpublished direct lesson retrieval denial and duplicate-completion protection; the browser test did not attempt to publish or access drafts as an unauthorized user.
- The admin UI reviews and transitions content but does not edit lesson text or upload packages; package creation/import is a CLI workflow. Reviewers must independently verify source documents; software cannot establish reviewer qualifications.
- Native Android/iOS, PostgreSQL runtime, formula rendering, offline learning, practice/revision sessions, notifications and broader accessibility testing remain unverified or incomplete.
- PostgreSQL/Docker/`psql` are unavailable in the implementation environment; local import and testing used SQLite.
