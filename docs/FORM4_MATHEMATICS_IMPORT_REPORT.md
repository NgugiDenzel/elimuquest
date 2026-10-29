# Form Four Mathematics Import Report

## Baseline and import status

The current repository already contains the Form 4 Mathematics draft import and the actual live database reflects it as draft-only content.

### Verified live counts

From the current SQLite database:

- Form 4 subjects: 1 (`mathematics-form-4`)
- Form 4 lessons: 10
- Form 4 questions: 50
- Form 4 published lessons: 0
- Grade 6 published lessons: 5
- Grade 6 published questions: 20

### Import package

- Directory: `backend/content-packages/math-curriculum-draft`
- Package files in the Form 4 set:
  - `form-4-matrices-and-transformations.json`
  - `form-4-statistics-ii.json`
  - `form-4-loci.json`
  - `form-4-trigonometry-iii.json`
  - `form-4-three-dimensional-geometry.json`
  - `form-4-longitudes-and-latitudes.json`
  - `form-4-linear-programming.json`
  - `form-4-differentiation.json`
  - `form-4-area-approximation.json`
  - `form-4-integration.json`

### Source reference pattern

Each lesson package uses the manuscript-based source reference format:

- `ElimuQuest Mathematics Curriculum Draft v1, PDF p. 16`
- `ElimuQuest Mathematics Curriculum Draft v1, PDF pp. 16-17`
- `ElimuQuest Mathematics Curriculum Draft v1, PDF p. 19`

This is a valid provenance trail within the current repository, but it is not proof of an official KICD syllabus match.

## Safety and idempotency

The importer logic in `backend/app/content/importer.py` is designed to:

- fail if a topic mapping is not registered,
- reject overwriting differing lesson content,
- keep draft imports separate from published content,
- avoid duplicate records when the same package is re-imported.

This means the Form 4 package is safe to re-run as a dry run or apply step without creating duplicates, provided the package remains unchanged.

## Publication state

The live database confirms that the Form Four Mathematics content is not published to learners. It remains in the review/draft pipeline, which matches the project’s safety requirement for unpublished content.

## Summary

The Form 4 notes are present, importable, and structurally valid. The repository is consistent with the current working state: imported as draft content for a legacy 8-4-4 pathway, not published, and not represented as official KICD material.
