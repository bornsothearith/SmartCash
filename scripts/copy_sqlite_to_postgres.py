"""SCG-35: copy the data in data/smartcash.db (SQLite) into PostgreSQL.

Copies users (with their password HASHES, never passwords), transactions,
and diary imports. Exchange rates are not copied: the app loads them from
data/exchange_rates.csv by itself.

Safe by default:
- Shows what it WOULD copy and stops, unless you add --yes.
- Refuses to run if the PostgreSQL database already has users (no double copy).

Run (DATABASE_URL comes from the environment or .streamlit/secrets.toml):
    python -m scripts.copy_sqlite_to_postgres            # dry run: counts only
    python -m scripts.copy_sqlite_to_postgres --yes      # really copy
"""
import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from smartcash import config  # noqa: E402
from smartcash.database.connection import connect_postgres  # noqa: E402

TABLES = {   # table -> columns to copy (same names in both databases)
    "users": ["id", "username", "password_hash", "failed_logins", "locked_until", "created_at"],
    "transactions": ["id", "user_id", "tx_date", "tx_type", "amount", "currency", "category",
                     "payment_method", "note", "is_demo", "created_at"],
    "diary_raw": ["id", "batch_id", "user_id", "row_number", "payload", "status", "reason"],
    "diary_import_keys": ["fingerprint", "user_id"],
}


def read_sqlite(path):
    src = sqlite3.connect(path)
    src.row_factory = sqlite3.Row
    have = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    data = {}
    for table, cols in TABLES.items():
        if table not in have:
            data[table] = []
            continue
        rows = [dict(r) for r in src.execute(f"SELECT {', '.join(cols)} FROM {table}")]
        if table == "transactions":
            # Sprint 1 rows have no owner: nobody can see them, so don't copy them.
            rows = [r for r in rows if r["user_id"] is not None]
        if table == "users":
            for r in rows:   # SQLite stores "YYYY-MM-DD HH:MM:SS" (UTC); make it explicit
                if r["created_at"] and "T" not in r["created_at"] and "+" not in r["created_at"]:
                    r["created_at"] = r["created_at"] + "+00"
        data[table] = rows
    src.close()
    return data


def copy(sqlite_path, url, really=False, out=print):
    data = read_sqlite(sqlite_path)
    for table in TABLES:
        out(f"{table}: {len(data[table])} rows")
    if not really:
        out("Dry run only. Add --yes to copy.")
        return data
    pg = connect_postgres(url)          # runs migrations first
    if pg.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]:
        raise SystemExit("PostgreSQL already has users. Stopping so nothing is copied twice.")
    try:
        for table, cols in TABLES.items():
            if not data[table]:
                continue
            override = " OVERRIDING SYSTEM VALUE" if table in ("users", "transactions") else ""
            sql = (f"INSERT INTO {table} ({', '.join(cols)}){override} "
                   f"VALUES ({', '.join('?' * len(cols))})")
            pg.executemany(sql, [tuple(r[c] for c in cols) for r in data[table]])
        # Make new ids continue after the copied ones.
        for table in ("users", "transactions"):
            pg.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                       f"COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)")
        pg.commit()
    except Exception:
        pg.rollback()
        raise
    finally:
        pg.close()
    out("Copied.")
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--sqlite", default=str(config.DB_PATH), help="SQLite file to copy from")
    ap.add_argument("--yes", action="store_true", help="really copy (default: dry run)")
    args = ap.parse_args()
    url = config.database_url()
    if not url:
        raise SystemExit("No DATABASE_URL. Put it in .streamlit/secrets.toml or the environment.")
    copy(args.sqlite, url, really=args.yes)


if __name__ == "__main__":
    main()
