# Phase Five Backup and Recovery Record

Audit date: 2026-10-29.

## Active database and backup

- Active database: `backend/elimuquest.db` (the configured relative SQLite URL resolves
  there when the backend is launched from `backend/`).
- Verified backup:
  `backend/backups/elimuquest-phase5-20261029-153833.db`
- Backup size: 716,800 bytes.
- Creation method: Python `sqlite3.Connection.backup()` from a read-only connection to the
  active database; no raw copy of a potentially live SQLite file was used.
- Backup integrity: `PRAGMA integrity_check` returned `ok`.
- Active database integrity: `ok`.
- Active and backup `PRAGMA foreign_key_check`: zero violations.

## Baseline and preservation evidence

| Table | Rows in active and backup | Row checksum comparison |
|---|---:|---|
| `users` | 2 | Identical |
| `answer_attempts` | 37 | Identical |
| `lesson_progress` | 10 | Identical |
| `lesson_sessions` | 30 | Identical |
| `xp_transactions` | 14 | Identical |
| `achievements` | 1 | Identical |
| `user_achievements` | 2 | Identical |
| `daily_activity` | 3 | Identical |

Stable SHA-256 checksums were computed over sorted row tuples. The checksum values are
retained in the session evidence; the report records equality and counts only, avoiding
unnecessary disclosure of user records.

The active database and backup both contain 17 subjects, 77 topics, 125 lessons, and 449
questions. No Phase Five operation changed the active database. The importer checks were
dry-runs, and API tests used an isolated in-memory database.

## Isolated restore test

The verified backup was restored with the SQLite backup API to a temporary file in a
separate temporary directory, never over the active database. The restored copy:

- passed `PRAGMA integrity_check` (`ok`);
- had zero `PRAGMA foreign_key_check` violations;
- matched the backup counts for subjects, topics, lessons, and questions.

The temporary restore copy was closed and removed after verification.

## Recovery procedure

1. Stop the API process before any operator-managed database replacement.
2. Preserve the current database and its SQLite WAL/SHM files, if present, as a separate
   recovery point. Do not overwrite or reset the active database as an exploratory step.
3. Restore the verified backup to a **new path** using Python's SQLite backup API.
4. Run `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, and compare expected counts on
   the new file.
5. Point `DATABASE_URL` to the verified restored file (or schedule an explicitly approved
   maintenance cutover); start the API and check `/health`, `/readiness`, authentication,
   lesson retrieval, and learner progress.
6. Keep both the previous active file and the verified backup until the recovered service
   has been validated. Do not delete the original as part of this phase.

For PostgreSQL deployments, use database-native backup and point-in-time recovery tools;
the SQLite backup cannot restore a PostgreSQL service.

## Rollback status

No database rows or schema were changed, so no rollback was necessary. The listed backup
is a verified recovery point, not permission to replace the active database.
