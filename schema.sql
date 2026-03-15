-- SQLite schema for the Glass Machinery bilingual website.
--
-- Goals:
-- - Keep tables explicitly named as requested: users, machines, specifications,
--   gallery_items, process_steps, inquiries, submissions.
-- - Support bilingual content per record where needed (en/ar) to avoid mixing
--   languages in one string.
-- - Support an approval workflow via `submissions` that stores proposed changes
--   as JSON payload (create/update/delete) and can be approved/rejected.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- USERS / AUTH / ROLES
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  username          TEXT NOT NULL UNIQUE,
  email             TEXT NOT NULL UNIQUE,
  password_hash     TEXT NOT NULL,
  -- Roles:
  -- - admin_developer: full admin + approve/reject submissions
  -- - developer: can create submissions and manage content within permissions
  role              TEXT NOT NULL CHECK (role IN ('admin_developer', 'developer')),
  is_active         INTEGER NOT NULL DEFAULT 1,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  last_login_at     TEXT
);

-- ---------------------------------------------------------------------------
-- MACHINES (public + admin managed)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS machines (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  slug              TEXT NOT NULL UNIQUE,
  title_en          TEXT NOT NULL,
  title_ar          TEXT NOT NULL,
  short_desc_en     TEXT NOT NULL,
  short_desc_ar     TEXT NOT NULL,
  long_desc_en      TEXT NOT NULL,
  long_desc_ar      TEXT NOT NULL,
  category          TEXT,
  image_path        TEXT, -- e.g. images/machines/glass_tempering_furnace.png
  is_featured       INTEGER NOT NULL DEFAULT 0,
  sort_order        INTEGER NOT NULL DEFAULT 0,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT
);

-- ---------------------------------------------------------------------------
-- SPECIFICATIONS (DB-driven table display)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS specifications (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  machine_id        INTEGER NOT NULL,
  -- We store structured specs in "field/value" rows so the table can be ordered.
  field_key         TEXT NOT NULL, -- internal key used in i18n labels
  value_en          TEXT NOT NULL,
  value_ar          TEXT NOT NULL,
  unit              TEXT,
  sort_order        INTEGER NOT NULL DEFAULT 0,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT,
  FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- GALLERY ITEMS (public gallery + captions)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gallery_items (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  machine_id        INTEGER,
  title_en          TEXT NOT NULL,
  title_ar          TEXT NOT NULL,
  description_en    TEXT NOT NULL,
  description_ar    TEXT NOT NULL,
  category          TEXT,
  image_path        TEXT NOT NULL, -- relative to /static/
  is_published      INTEGER NOT NULL DEFAULT 1,
  sort_order        INTEGER NOT NULL DEFAULT 0,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT,
  FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------------
-- PROCESS STEPS (How it works page)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS process_steps (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  step_no           INTEGER NOT NULL,
  title_en          TEXT NOT NULL,
  title_ar          TEXT NOT NULL,
  description_en    TEXT NOT NULL,
  description_ar    TEXT NOT NULL,
  icon              TEXT, -- optional icon class / identifier
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at        TEXT
);

-- ---------------------------------------------------------------------------
-- INQUIRIES (Contact form storage)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inquiries (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  name              TEXT NOT NULL,
  email             TEXT NOT NULL,
  phone             TEXT,
  message           TEXT NOT NULL,
  preferred_lang    TEXT NOT NULL CHECK (preferred_lang IN ('en', 'ar')) DEFAULT 'en',
  source_page       TEXT,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  status            TEXT NOT NULL CHECK (status IN ('new', 'in_review', 'closed')) DEFAULT 'new'
);

-- ---------------------------------------------------------------------------
-- SUBMISSIONS (Review / approval workflow)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS submissions (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  created_by_user_id INTEGER NOT NULL,
  -- target_table: which table the change applies to
  target_table      TEXT NOT NULL CHECK (target_table IN ('machines','specifications','gallery_items','process_steps','users')),
  action            TEXT NOT NULL CHECK (action IN ('create','update','delete')),
  -- target_id: the row id in the target table (null for create)
  target_id         INTEGER,
  payload_json      TEXT NOT NULL, -- JSON dict with proposed fields/values
  status            TEXT NOT NULL CHECK (status IN ('pending','approved','rejected')) DEFAULT 'pending',
  reviewer_user_id  INTEGER,
  reviewer_note     TEXT,
  created_at        TEXT NOT NULL DEFAULT (datetime('now')),
  reviewed_at       TEXT,
  FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (reviewer_user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_specs_machine ON specifications(machine_id);
CREATE INDEX IF NOT EXISTS idx_gallery_published ON gallery_items(is_published);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);

