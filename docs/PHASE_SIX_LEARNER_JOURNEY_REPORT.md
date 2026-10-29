# Phase Six Synthetic Learner Journey Report

**Date:** 2026-10-29  
**Test data:** Disposable synthetic account and isolated SQLite database; no active users
or learner activity were copied.

## API journeys

The isolated database contained the 17-subject/77-topic/125-lesson/449-question
curriculum catalog and one achievement definition. Before the test it contained zero
users, sessions, attempts, progress rows, XP transactions, user achievements, and daily
activity rows.

One synthetic learner registered, logged in, selected each supported level, opened the
published Mathematics learning path and lesson, submitted every answer from the isolated
test fixture, and completed the lesson.

| Selection | Subjects returned | Mathematics lessons | Lesson completed | Questions | Score | XP |
|---|---:|---:|---|---:|---:|---:|
| CBC/CBE Grade 6 | 4 | 13 | Whole Numbers | 9 | 100% | 55 |
| CBC/CBE Grade 9 | 4 | 18 | Integers | 7 | 100% | 45 |
| 8-4-4 Form 4 | 5 | 10 | Matrices and Transformations | 7 | 100% | 45 |

The selected curriculum/level on every returned subject and lesson matched the learner's
selection. Unauthenticated subject access returned HTTP 401. A Grade 6 lesson requested
while the account was selected into Grade 9 returned HTTP 404. Progress and dashboard
responses reflected the stored completions and 145 XP. The synthetic API server was
restarted; login and the stored Grade 9 progress/XP were still available afterward.

## Browser journey

Against the same isolated database, the web app:

1. Logged in as the synthetic learner and displayed the Grade 9 CBC/CBE dashboard.
2. Opened Mathematics, showing 18 published lessons.
3. Opened the learning path and displayed the published lesson list.
4. Opened “Cubes and Cube Roots,” read its explanation and saw its first practice question.
5. Accepted `125` for `5^3` and displayed “That's correct!”
6. Reloaded the lesson route and restored the authenticated lesson view.

The browser check initially exposed that detail routes nested under the tab navigator
returned to the dashboard. The screens were moved to an authenticated root-stack route
group, and the route group waits for auth hydration before rendering protected queries.
The same browser journey then opened the subject, path, and lesson and survived refresh.

## Limitations

This verifies a local synthetic web journey and API behavior, not native iOS/Android,
accessibility, production TLS, real-device LAN access, third-party analytics, or expert
review of lesson content. The synthetic database was not the active database and is
scheduled for deletion after verification.
