-- SmartCash PostgreSQL schema for SCG-35.
-- SCG-36 raw storage is also installed by the application startup migration.
-- Store DATABASE_URL in Streamlit secrets or an environment variable.

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    failed_logins INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    tx_date TEXT NOT NULL,
    tx_type TEXT NOT NULL CHECK (tx_type IN ('expense', 'income')),
    amount DOUBLE PRECISION NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL CHECK (currency IN ('USD', 'KHR')),
    category TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    note TEXT DEFAULT '',
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_date TEXT PRIMARY KEY,
    khr_per_usd DOUBLE PRECISION NOT NULL CHECK (khr_per_usd > 0),
    source TEXT NOT NULL,
    is_filled INTEGER NOT NULL DEFAULT 0 CHECK (is_filled IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_date
    ON transactions (user_id, tx_date);

CREATE TABLE IF NOT EXISTS diary_raw (
    id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS diary_import_keys (
    fingerprint TEXT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
);
