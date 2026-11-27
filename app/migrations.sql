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

-- GOLF-17 / GOLF-18: golfer profile, shown to instructors with each booking (GOLF-20).
CREATE TABLE IF NOT EXISTS student_profiles (
  user_id INTEGER PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
  handicap REAL,                          -- 0 to 54 (World Handicap System); NULL = no handicap yet
  level TEXT NOT NULL DEFAULT 'Beginner' CHECK (level IN ('Beginner', 'Intermediate', 'Advanced')),
  goals TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- GOLF-48 / GOLF-49: notes the instructor writes after a lesson; the golfer can read them.
CREATE TABLE IF NOT EXISTS lesson_notes (
  booking_id INTEGER PRIMARY KEY REFERENCES bookings (id) ON DELETE CASCADE,
  notes TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
