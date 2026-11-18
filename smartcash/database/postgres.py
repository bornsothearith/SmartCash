"""SCG-35 PostgreSQL support.

The rest of the app was written for SQLite. This adapter lets the SAME code
run on PostgreSQL:
- SQL uses "?" placeholders -> turned into psycopg's "%s".
- Rows come back as dicts with plain Python values, like SQLite gives:
  DATE -> "YYYY-MM-DD", NUMERIC -> float, TIMESTAMP -> ISO text.
- A connection closed by the server (Neon sleeps when idle) is reopened once.
- A failed statement rolls back, so the next statement still works
  (PostgreSQL refuses all statements after an error until rollback).
- Read-only statements end their transaction straight away, so the app never
  sits "idle in transaction" between page clicks.

Schema changes live in migrations/NNN_name.sql and run once, in order;
applied files are recorded in the schema_migrations table.
"""
import datetime as dt
from decimal import Decimal
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def _plain(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    return value


class Row(dict):
    """A dict that also allows row[0], like sqlite3.Row."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class Cursor:
    def __init__(self, cur):
        self._cur = cur
        self.rowcount = cur.rowcount

    def _wrap(self, row):
        return None if row is None else Row({k: _plain(v) for k, v in row.items()})

    def fetchone(self):
        return self._wrap(self._cur.fetchone()) if self._cur.description else None

    def fetchall(self):
        return [self._wrap(r) for r in self._cur.fetchall()] if self._cur.description else []

    def __iter__(self):
        return iter(self.fetchall())


def _to_psycopg(sql):
    # A literal % must be doubled for psycopg; then ? placeholders become %s.
    return sql.replace("%", "%%").replace("?", "%s")


class PostgresConnection:
    """Small SQLite-style wrapper around one psycopg connection."""

    def __init__(self, url):
        try:
            import psycopg  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("Install psycopg[binary] to use PostgreSQL.") from exc
        self._url = url
        self._savepoints = 0
        self._dirty = False
        self._open()

    def _open(self):
        import psycopg
        from psycopg.rows import dict_row
        # prepare_threshold=None: no server-side prepared statements, so Neon's
        # pooled connection string (PgBouncer) works as well as the direct one.
        self._conn = psycopg.connect(self._url, row_factory=dict_row, connect_timeout=15,
                                     prepare_threshold=None)
        self._savepoints = 0
        self._dirty = False

    @property
    def closed(self):
        return self._conn.closed

    def execute(self, sql, params=()):
        import psycopg
        head = sql.lstrip().split(None, 1)[0].upper() if sql.strip() else ""
        try:
            cur = self._conn.execute(_to_psycopg(sql), params)
        except psycopg.OperationalError:
            # Server closed the connection (e.g. Neon was asleep). Reopen and retry once,
            # but only if nothing unsaved would be lost.
            if self._dirty or self._savepoints:
                raise
            self._open()
            cur = self._conn.execute(_to_psycopg(sql), params)
        except psycopg.Error:
            if not self._savepoints:
                self.rollback()
            raise

        if head == "SAVEPOINT":
            self._savepoints += 1
        elif head == "RELEASE":
            self._savepoints = max(0, self._savepoints - 1)
        elif head not in ("SELECT", "WITH", "ROLLBACK"):
            self._dirty = True
        result = Cursor(cur)
        if head in ("SELECT", "WITH") and not self._dirty and not self._savepoints:
            self._conn.commit()   # results are already fetched; end the read-only transaction
        return result

    def executemany(self, sql, seq):
        with self._conn.cursor() as cur:
            cur.executemany(_to_psycopg(sql), seq)
        self._dirty = True

    def commit(self):
        self._conn.commit()
        self._dirty = False
        self._savepoints = 0

    def rollback(self):
        self._conn.rollback()
        self._dirty = False
        self._savepoints = 0

    def close(self):
        self._conn.close()


def migration_files():
    return sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"))


def migrate(conn):
    """Apply every migrations/NNN_*.sql not yet applied. Returns the names applied."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations ("
                 " name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
    conn.commit()
    done = {r["name"] for r in conn.execute("SELECT name FROM schema_migrations")}
    applied = []
    for path in migration_files():
        if path.name in done:
            continue
        try:
            conn._conn.execute(path.read_text(encoding="utf-8"))   # whole file, one transaction
            conn.execute("INSERT INTO schema_migrations (name) VALUES (?)", (path.name,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        applied.append(path.name)
    return applied
