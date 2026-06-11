CREATE TABLE IF NOT EXISTS check_in_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id TEXT NOT NULL UNIQUE,
    name TEXT DEFAULT '',
    check_in_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'checked_in'
);
