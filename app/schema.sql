-- SwingSlot database schema (SQLite)
-- Running this file resets the database. Tables added after the MVP live in migrations.sql.

DROP TABLE IF EXISTS lesson_notes;
DROP TABLE IF EXISTS student_profiles;
DROP TABLE IF EXISTS cancellations;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS time_slots;
DROP TABLE IF EXISTS instructor_profiles;
DROP TABLE IF EXISTS users;

-- Every account is either a golfer ("student") or an "instructor".
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('student', 'instructor')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Public profile shown to golfers before they book (GOLF-7).
CREATE TABLE instructor_profiles (
  user_id INTEGER PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
  location TEXT NOT NULL DEFAULT '',
  bio TEXT NOT NULL DEFAULT '',
  lesson_types TEXT NOT NULL DEFAULT '',  -- comma-separated, e.g. "Full Swing,Putting"
  price INTEGER NOT NULL DEFAULT 50,
  lat REAL,
  lon REAL
);

-- Open times an instructor can teach (GOLF-22).
CREATE TABLE time_slots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instructor_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  starts_at TEXT NOT NULL,                -- ISO format "YYYY-MM-DDTHH:MM"
  UNIQUE (instructor_id, starts_at)
);

-- A booked slot (GOLF-32). UNIQUE(slot_id) stops two golfers booking the same slot.
CREATE TABLE bookings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slot_id INTEGER NOT NULL UNIQUE REFERENCES time_slots (id) ON DELETE CASCADE,
  student_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
