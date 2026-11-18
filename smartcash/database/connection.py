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

POSTGRES_TABLES = """
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
    is_demo INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_date TEXT PRIMARY KEY,
    khr_per_usd DOUBLE PRECISION NOT NULL CHECK (khr_per_usd > 0),
    source TEXT NOT NULL,
    is_filled INTEGER NOT NULL DEFAULT 0 CHECK (is_filled IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_tx_user_date ON transactions (user_id, tx_date);
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


class PostgresConnection:
    """Small qmark-compatible adapter for the existing database API."""

    def __init__(self, url):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("Install psycopg[binary] to use PostgreSQL.") from exc
        self._conn = psycopg.connect(url, row_factory=dict_row)

    def execute(self, sql, params=()):
        return self._conn.execute(sql.replace("?", "%s"), params)

    def executemany(self, sql, params):
        """Execute a parameterized statement for each row using a cursor.

        psycopg 3 exposes ``executemany`` on cursors, not on the connection
        object. The SQLite and PostgreSQL adapters share this method so rate
        synchronization and imports work with either backend.
        """
        with self._conn.cursor() as cursor:
            return cursor.executemany(sql.replace("?", "%s"), params)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def rollback(self):
        self._conn.rollback()


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


def connect(path=None):
    if path is None and config.database_url():
        conn = PostgresConnection(config.database_url())
        for statement in POSTGRES_TABLES.split(";"):
            if statement.strip():
                conn.execute(statement)
        conn.commit()
        conn.execute(IMPORT_TABLES)
        conn.execute(IMPORT_KEYS)
        conn.commit()
        if config.RATES_CSV.exists():
            rates.sync_rates(conn)
        return conn
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
