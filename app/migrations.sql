-- Tables added after the MVP (Sprint 3).
-- Every statement uses IF NOT EXISTS, so this file runs safely on every start-up:
-- on a brand-new database and on one that was created before these features existed.

-- GOLF-37 / GOLF-41: cancelled lessons, kept so the instructor can see what was cancelled.
CREATE TABLE IF NOT EXISTS cancellations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instructor_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  student_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  starts_at TEXT NOT NULL,                -- when the cancelled lesson was going to start
  cancelled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
