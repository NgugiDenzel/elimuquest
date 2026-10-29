# Structured lesson packages

Packages are JSON documents validated by `app.content.schema.ContentPackage` (schema version `1.0`). The importer resolves curriculum system, level, version, subject slug and source ID against `app.curriculum.catalog`; unsupported subject/level pairings fail validation.

## Fields

- Top-level `curriculum_system`, `curriculum_level`, `curriculum_version`, `subject_slug`, `topic_slug`, `topic_name`, topic `source_reference`, and `source_id` identify the curriculum mapping and source provenance.
- Top-level `ai_generated` records AI assistance explicitly. Imports always remain drafts, regardless of this flag.
- `is_demo` distinguishes demonstration material from imported learning content. `false` is the default.
- Each lesson has a stable slug, content version and order, title/summary/content, optional learning objectives and worked examples, structured explanation sections, an author, a precise source reference, and questions.
- Multiple-choice and short-answer questions are supported. Multiple-choice answers must match one of the non-empty unique options and include an explanation. Short-answer questions have no options; answers are compared case-insensitively after whitespace normalization, the Unicode minus sign is treated as a hyphen-minus, and one final period is ignored. A wrong answer reveals the stored answer after submission when no explanation was supplied.
- Source packages may omit learning objectives or separate worked examples when the source manuscript does not provide them; their explanatory text must still be stored in an explanation section.
- Duplicate lesson slugs, duplicate normalized question prompts, unsupported mappings, invalid answer keys, missing explanation sections, and conflicting existing content are rejected.

## Coverage authoring standard

The importer has **no two-lesson limit**: a package may contain every lesson validated by `ContentPackage.lessons`, and directory imports process every JSON file. The two-lesson pattern in earlier subject batches came from authoring choices, not a database, review, API, or learner-screen cap. Do not equate one imported package or a small starter set with course coverage.

For a supported subject/level, plan an initial minimum of **8 substantial lessons across at least 3 distinct topics**. Increase the target to 10–12 or more when the discipline and available trustworthy materials warrant it; mathematics and sciences usually require broader topic distribution. This is a planning floor, not a completeness or official-alignment claim. The audit matrix must track topic count, total lessons, published lessons, questions, target, and remaining gaps by exact curriculum system, level, version, and subject. Keep 8-4-4 Form 4 separate from CBC/CBE Grade 10, and author only levels registered in `app.curriculum.catalog`.

Content batches should define learning outcomes and distinct topic coverage before writing. Each lesson should have explicit objectives, at least two explanatory sections, a worked example or practical illustration, and a concise learner recap in its explanation. Include at least three answer-checked practice questions when suitable. Avoid repetitive variants made only to reach a count. Record original/supplementary status and source/license provenance honestly; never invent citations or official approval. Review each package with the importer dry-run and inspect every rejected file before applying a directory transaction. A successful import creates drafts only; publication still requires the authenticated reviewer workflow.

## Import behavior

Run from `backend` with the database migrated and mapped subjects seeded:

```powershell
python -m app.content.importer .\content-packages\your-package.json
python -m app.content.importer .\content-packages\your-package.json --apply
python -m app.content.importer .\content-packages\math-curriculum-draft
python -m app.content.importer .\content-packages\math-curriculum-draft --apply
```

The default is a read-only dry run. A directory import processes its JSON files in one transaction; a failure rolls back the whole directory. `--apply` creates only draft lessons. Exact repeat imports are idempotent; a changed package cannot overwrite an existing lesson, especially published content. Package `sort_order` preserves the source lesson sequence. For a revised lesson, use a new stable slug (for example, a `-v2` suffix) and increment `content_version`; the original version remains immutable and retains learner progress.

Draft → In review → Approved → Published → Archived transitions are admin-only via `PATCH /api/v1/admin/lessons/{lesson_id}/status`. The backend checks explanation sections, valid answer formats and provenance fields, and requires a reviewer different from the author before approval. Learning objectives and separate worked examples remain optional because a source may not supply them. The backend does not independently establish that an external PDF was read or that a reviewer is a qualified subject-matter expert; that human verification must be recorded and audited outside this prototype. Published learner endpoints require both `published=true` and `content_status=published`.

`example-grade-9.json` is intentionally a fixture, not curriculum content. Its placeholder provenance is rejected by validation until replaced with precise citations. Do not treat the fixture as mapped content or review, approve, or publish it.

## Supplied Mathematics draft

`math-curriculum-draft/` contains 36 packages extracted from the user-supplied *ElimuQuest Mathematics Curriculum Draft* (21 pages; version label v1; authored by ElimuQuest). The packages preserve the manuscript's lesson ordering, explanatory text and answer keys: Grade 6 has 8 lessons/48 questions, Grade 9 has 18 lessons/86 questions, and Form 4 has 10 lessons/50 questions.

This is a user-provided draft, not an official KICD or Ministry syllabus. Its PDF page references establish provenance to that manuscript only; they do not establish official strands, outcomes, or alignment. The source does not provide a separately structured objective list, worked-example records, or per-question explanations, so those fields are not invented. These imports remain unpublished drafts until an authorized, qualified reviewer independently verifies the official curriculum mapping and approves publication.

Validate the complete set before applying it:

```powershell
python -m app.content.importer .\content-packages\math-curriculum-draft
python -m app.content.importer .\content-packages\math-curriculum-draft --apply
```

The directory operation is atomic. Repeating the apply command reports the existing packages as unchanged.

## Grade 6 Whole Numbers pupil-book excerpt

`grade6-whole-numbers-pupils-book.json` contains five ordered lessons for Grade 6 Mathematics, Strand 1: Numbers, Sub-strand 1.1: Whole Numbers, based on the user-supplied six-page *Grade 6 Mathematics: Pupil’s Book* PDF. It preserves the supplied step text, worked examples, activities, review text, and practice questions. The eight printed questions are divided into 20 quiz items across the five topic lessons.

The supplied excerpt says its answers are in the answer key at the end of Strand 1, but the key is not included in the six-page file. The stored marking answers were calculated independently from the questions and methods; they are not represented as answers supplied by the book. Each lesson's source reference and the admin review screen disclose this. A reviewer must verify the calculated keys before production publication.

Validate and import the module using the normal draft-only workflow:

```powershell
python -m app.content.importer .\content-packages\grade6-whole-numbers-pupils-book.json
python -m app.content.importer .\content-packages\grade6-whole-numbers-pupils-book.json --apply
```

The apply is idempotent and leaves all five lessons unpublished until an authorized reviewer approves and publishes them.
