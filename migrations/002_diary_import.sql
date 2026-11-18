-- SCG-36: raw storage for imported diary rows + duplicate keys (PostgreSQL).
-- Applied once after 001; recorded in schema_migrations.

CREATE TABLE diary_raw (
    id         TEXT PRIMARY KEY,                 -- uuid
    batch_id   TEXT NOT NULL,                    -- one upload = one batch
    user_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    payload    TEXT NOT NULL,                    -- the original CSV row as JSON
    status     TEXT NOT NULL,                    -- pending / imported / duplicate / rejected
    reason     TEXT NOT NULL DEFAULT ''
);
CREATE INDEX diary_raw_user ON diary_raw (user_id, status);

CREATE TABLE diary_import_keys (
    fingerprint TEXT PRIMARY KEY,                -- sha256 of user + transaction fields
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
);
