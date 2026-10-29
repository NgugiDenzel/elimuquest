# Phase Six Backup and Recovery Report

**Verification date:** 2026-10-29  
**Active database:** `backend/elimuquest.db`  
**Backup:** `backend/backups/elimuquest-phase6-20261029-161747.db`

## Backup verification

The timestamped backup is 716,800 bytes. Both the active database and backup returned
`ok` from SQLite `PRAGMA integrity_check`; both had zero `PRAGMA foreign_key_check`
violations.

| Table | Active | Backup |
|---|---:|---:|
| subjects | 17 | 17 |
| topics | 77 | 77 |
| lessons | 125 | 125 |
| lesson_questions | 449 | 449 |
| users | 2 | 2 |
| answer_attempts | 37 | 37 |
| lesson_progress | 10 | 10 |
| lesson_sessions | 30 | 30 |
| xp_transactions | 14 | 14 |
| achievements | 1 | 1 |
| user_achievements | 2 | 2 |
| daily_activity | 3 | 3 |

Rows in each of the eight tracked learner-data tables were compared in stable primary-key
order; active and backup values matched exactly. An isolated restore of the backup also
passed integrity, foreign-key, and table-count checks. The active database was not reset
or rewritten.

## Phase Six test-data isolation

The authenticated journey used a separate temporary database populated only with
subjects, topics, lessons, questions, and achievement definitions. Its learner tables
were verified empty before registration. All subsequent synthetic user, attempt, progress,
session, and XP records were confined to that temporary database.

The temporary database is disposable and is not a production backup. No deployment,
restore-over-active, or learner-data migration was performed.
