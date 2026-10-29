# Form Four Mathematics Content Issues

## Summary

The current repository contains a draft-only Form Four Mathematics import sourced from the user-supplied PDF `MATHS FORM 4 NOTES.pdf`. The material is present and structured, but it remains unverified as an official KICD or Ministry syllabus.

## Active issues

1. Official syllabus edition is unresolved.
   - The live repo tracks `8_4_4` Form 4 Mathematics under `KICD-844`, but the underlying official KICD PDF/edition has not been identified and cited in the working implementation.
   - The register explicitly marks the official Form 4 curriculum mapping as still unresolved.

2. Source provenance is manuscript-based, not official-boundary verified.
   - The importer package references `ElimuQuest Mathematics Curriculum Draft v1` rather than a verified KICD syllabus publication.
   - This is a content provenance record, not proof of official curriculum alignment.

3. Answer keys are not official.
   - The current implementation distinguishes source notes content from independently calculated answers.
   - The app keeps this material in the admin review mechanism and does not turn it into an official marking-scheme assertion.

4. Learner visibility remains blocked.
   - The database currently shows `content_status = 'draft'` and `published = 0` for all Form Four lessons.
   - The backend enforces publication gating, so the material remains hidden from ordinary learners.

5. Human review is still required.
   - The draft is structurally valid and appears consistent with the PDF notes, but it still requires a qualified reviewer to confirm educational appropriateness, topic coverage and publication readiness.

## Confirmed repository facts

- Import package directory: `backend/content-packages/math-curriculum-draft`
- Form 4 lesson count in the live DB: 10
- Form 4 question count in the live DB: 50
- Publication status: unpublished draft
- Grade 6 module: published and separate from the Form 4 draft set

## Recommended handling

- Keep the content as a draft until the official Form Four syllabus source is reviewed.
- Maintain the current split between legacy Form 4 and CBC/CBE Senior School content.
- Do not label any imported answer as an official KICD or KCSE marking-scheme answer.
- Continue to use the signed-in admin/publication workflow for any future approval.
