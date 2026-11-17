"""SQLite connection and tables.

Local SQLite file for now (data/smartcash.db, never on GitHub).
It moves to PostgreSQL in SCG-35.
"""
import sqlite3

from smartcash import config, rates

TABLES = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,              -- scrypt hash, never the password
    failed_logins INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,                        -- set after too many wrong passwords
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tx_date TEXT NOT NULL,
    tx_type TEXT NOT NULL CHECK (tx_type IN ('expense', 'income')),
    amount REAL NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL CHECK (currency IN ('USD', 'KHR')),
    category TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    note TEXT DEFAULT '',
    is_demo INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_date TEXT PRIMARY KEY,
    khr_per_usd REAL NOT NULL CHECK (khr_per_usd > 0),
    source TEXT NOT NULL,
    is_filled INTEGER NOT NULL DEFAULT 0 CHECK (is_filled IN (0, 1))
);
"""


def _add_user_id_to_old_table(conn):
    """Databases made in Sprint 1 have no user_id column. Add it.

    Old rows keep user_id = NULL, so no user can see them.
    """
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(transactions)")}
    if "user_id" not in cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER REFERENCES users(id)")


def connect(path=None):
    conn = sqlite3.connect(path or config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(TABLES)
    _add_user_id_to_old_table(conn)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_user_date ON transactions (user_id, tx_date)")
    conn.commit()
    if config.RATES_CSV.exists():
        rates.sync_rates(conn)
    return conn
