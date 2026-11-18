"""Database connection: PostgreSQL when DATABASE_URL is set, else local SQLite.

- PostgreSQL (SCG-35): hosted database, data survives app restarts. Tables come
  from migrations/*.sql (see smartcash/database/postgres.py).
- SQLite: local file data/smartcash.db for development and tests
  (never on GitHub). Tables are created below.
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

IMPORT_TABLES = """
CREATE TABLE IF NOT EXISTS diary_raw (
    id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT ''
);
"""

IMPORT_KEYS = """
CREATE TABLE IF NOT EXISTS diary_import_keys (
    fingerprint TEXT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
);
"""


def _add_user_id_to_old_table(conn):
    """Databases made in Sprint 1 have no user_id column. Add it.

    Old rows keep user_id = NULL, so no user can see them.
    """
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(transactions)")}
    if "user_id" not in cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER REFERENCES users(id)")


def _migrate_exchange_rates(conn):
    """Add exchange-rate columns introduced after the first database version."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(exchange_rates)")}
    if "source" not in columns:
        conn.execute(
            "ALTER TABLE exchange_rates ADD COLUMN source TEXT NOT NULL DEFAULT 'legacy'"
        )
    if "is_filled" not in columns:
        conn.execute(
            "ALTER TABLE exchange_rates ADD COLUMN is_filled INTEGER NOT NULL DEFAULT 0"
        )


_pg_ready = set()   # database URLs already migrated + rates synced in this process


def connect_postgres(url):
    """Open PostgreSQL. The first time per URL (per app process): run migrations
    and copy the exchange rates. Later calls just open a connection."""
    from smartcash.database.postgres import PostgresConnection, migrate
    conn = PostgresConnection(url)
    if url not in _pg_ready:
        migrate(conn)
        if config.RATES_CSV.exists():
            rates.sync_rates(conn)
        _pg_ready.add(url)
    return conn


def connect(path=None):
    """path given -> that SQLite file (tests). Else PostgreSQL if DATABASE_URL is set,
    else the local SQLite file."""
    if path is None and config.database_url():
        return connect_postgres(config.database_url())
    conn = sqlite3.connect(path or config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(TABLES)
    conn.executescript(IMPORT_TABLES)
    conn.executescript(IMPORT_KEYS)
    _add_user_id_to_old_table(conn)
    _migrate_exchange_rates(conn)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_user_date ON transactions (user_id, tx_date)")
    conn.commit()
    if config.RATES_CSV.exists():
        rates.sync_rates(conn)
    return conn
