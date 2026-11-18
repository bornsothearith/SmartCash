"""SCG-35: the app on a REAL PostgreSQL database.

Skipped unless SMARTCASH_TEST_PG_URL points to an EMPTY throwaway database, e.g.
    set SMARTCASH_TEST_PG_URL=postgresql://tester@localhost:55432/smartcash_test
Every test wipes that database first. Never point it at the real (Neon) database.
"""
import io
import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from smartcash import auth, config, diary_import, rates
from smartcash import transactions as tx
from smartcash.database import connection
from smartcash.database.postgres import migrate, migration_files

URL = os.environ.get("SMARTCASH_TEST_PG_URL")
pytestmark = pytest.mark.skipif(not URL, reason="set SMARTCASH_TEST_PG_URL to test PostgreSQL")
PW = "secret123"
FIXTURES = Path(__file__).parent / "fixtures"


def _wipe():
    import psycopg
    with psycopg.connect(URL, autocommit=True) as c:
        c.execute("DROP SCHEMA public CASCADE")
        c.execute("CREATE SCHEMA public")
    connection._pg_ready.clear()


@pytest.fixture
def pg():
    _wipe()
    conn = connection.connect_postgres(URL)
    yield conn
    conn.close()


@pytest.fixture
def uid(pg):
    return auth.create_user(pg, "pg_user", PW, PW)


# ---------------- schema ----------------
def test_migrations_create_tables_with_right_types(pg):
    cols = {(r["table_name"], r["column_name"]): r["data_type"] for r in pg.execute(
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'public'")}
    assert cols[("transactions", "amount")] == "numeric"
    assert cols[("transactions", "tx_date")] == "date"
    assert cols[("exchange_rates", "rate_date")] == "date"
    assert cols[("exchange_rates", "khr_per_usd")] == "numeric"
    for table in ("transactions", "diary_raw", "diary_import_keys"):
        assert (table, "user_id") in cols
    names = [r["name"] for r in pg.execute("SELECT name FROM schema_migrations ORDER BY name")]
    assert names == [p.name for p in migration_files()]


def test_migrations_run_only_once(pg):
    assert migrate(pg) == []          # second time: nothing to do, no error


def test_rates_loaded_without_gaps(pg):
    days = [date.fromisoformat(r["rate_date"]) for r in
            pg.execute("SELECT rate_date FROM exchange_rates ORDER BY rate_date")]
    assert days[0] == min(rates.read_rates_csv())
    assert all(b - a == timedelta(days=1) for a, b in zip(days, days[1:]))


# ---------------- accounts ----------------
def test_usernames_ignore_case(pg):
    auth.create_user(pg, "Sokha", PW, PW)
    with pytest.raises(auth.SignupError, match="taken"):
        auth.create_user(pg, "sokha", PW, PW)
    assert auth.login(pg, "SOKHA", PW)["username"] == "Sokha"


def test_wrong_password_and_lockout(pg):
    auth.create_user(pg, "sokha", PW, PW)
    now = __import__("datetime").datetime(2026, 11, 18, 9, 0)
    for _ in range(auth.MAX_FAILED_LOGINS):
        with pytest.raises(auth.LoginError):
            auth.login(pg, "sokha", "wrongpass1", now=now)
    with pytest.raises(auth.LoginError, match="Too many"):
        auth.login(pg, "sokha", PW, now=now)
    assert auth.login(pg, "sokha", PW, now=now + timedelta(minutes=6))


# ---------------- transactions ----------------
def test_add_filter_edit_delete_and_values_look_like_sqlite(pg, uid):
    t = tx.Transaction(date(2026, 11, 14), "expense", 8000, "KHR", "Transport", "Cash", "bus")
    row_id = tx.add_transaction(pg, uid, t)
    row = tx.filter_transactions(pg, uid)[0]
    assert row["tx_date"] == "2026-11-14" and isinstance(row["amount"], float)
    assert tx.to_usd(row["amount"], row["currency"], row["tx_date"]) > 0
    tx.update_transaction(pg, uid, row_id, tx.Transaction(
        date(2026, 11, 14), "income", 50, "USD", "Gift", "Cash", "edited"))
    row = tx.filter_transactions(pg, uid, tx_types=["income"])[0]
    assert (row["amount"], row["note"]) == (50.0, "edited")
    tx.delete_transaction(pg, uid, row_id)
    assert tx.filter_transactions(pg, uid) == []


def test_filters_by_date_and_category(pg, uid):
    tx.load_demo_data(pg, uid, n=40)
    start, end = date.today() - timedelta(days=10), date.today()
    got = tx.filter_transactions(pg, uid, start, end, ["Transport"], ["expense"])
    assert all(r["category"] == "Transport" and start.isoformat() <= r["tx_date"] for r in got)


def test_users_cannot_touch_each_others_rows(pg, uid):
    other = auth.create_user(pg, "other_user", PW, PW)
    row_id = tx.add_transaction(pg, uid, tx.Transaction(date.today(), "expense", 3, "USD",
                                                        "Transport", "Cash"))
    with pytest.raises(ValueError):
        tx.delete_transaction(pg, other, row_id)
    assert tx.filter_transactions(pg, other) == []


def test_demo_data_reset(pg, uid):
    tx.reset_demo_data(pg, uid)
    tx.reset_demo_data(pg, uid)
    assert len(tx.filter_transactions(pg, uid)) == tx.DEMO_EXPENSES + tx.DEMO_INCOME


def test_bad_amount_is_rejected_and_connection_still_works(pg, uid):
    with pytest.raises(Exception):   # CHECK (amount > 0) in the database itself
        pg.execute("INSERT INTO transactions (user_id, tx_date, tx_type, amount, currency,"
                   " category, payment_method) VALUES (?, '2026-11-01', 'expense', -1, 'USD',"
                   " 'Transport', 'Cash')", (uid,))
    assert tx.filter_transactions(pg, uid) == []   # no "transaction is aborted" error


# ---------------- data survives a restart ----------------
def test_data_survives_restart(pg, uid):
    tx.add_transaction(pg, uid, tx.Transaction(date.today(), "income", 25, "USD", "Allowance", "Cash"))
    pg.close()
    connection._pg_ready.clear()           # like a brand-new app process
    again = connection.connect_postgres(URL)
    assert auth.login(again, "pg_user", PW)["id"] == uid
    assert tx.filter_transactions(again, uid)[0]["amount"] == 25.0
    again.close()


def test_reconnects_after_server_closed_connection(pg, uid):
    pg._conn.close()                        # e.g. Neon went to sleep
    assert tx.filter_transactions(pg, uid) == []


# ---------------- import ----------------
@pytest.mark.parametrize("name", ["diary_standard.csv", "diary_google_form.csv"])
def test_import_csv(pg, uid, name):
    content = (FIXTURES / name).read_bytes()
    first = diary_import.import_csv(pg, uid, io.BytesIO(content))
    again = diary_import.import_csv(pg, uid, io.BytesIO(content))
    assert first["imported"] == 1 and again["duplicates"] == 1
    assert pg.execute("SELECT COUNT(*) AS n FROM diary_raw").fetchone()["n"] == 2


def test_import_rejects_bad_row_and_keeps_going(pg, uid):
    csv = ("tx_date,tx_type,amount,currency,category,payment_method\n"
           "2026-11-01,expense,0,USD,Transport,Cash\n"
           "2026-11-02,expense,2,USD,Transport,Cash\n")
    result = diary_import.import_csv(pg, uid, io.StringIO(csv))
    assert result["imported"] == 1 and len(result["rejected"]) == 1


# ---------------- copy current SQLite data ----------------
def test_copy_sqlite_to_postgres(tmp_path):
    from scripts.copy_sqlite_to_postgres import copy
    from smartcash import db
    src_path = tmp_path / "old.db"
    src = db.connect(src_path)
    a = auth.create_user(src, "keep_me", PW, PW)
    tx.add_transaction(src, a, tx.Transaction(date(2026, 11, 3), "expense", 12000, "KHR",
                                              "Groceries", "Cash", "market"))
    diary_import.import_csv(src, a, io.BytesIO((FIXTURES / "diary_standard.csv").read_bytes()))
    src.close()
    _wipe()
    copy(src_path, URL, really=True, out=lambda *_: None)
    pg = connection.connect_postgres(URL)
    user = auth.login(pg, "keep_me", PW)                       # same password still works
    rows = tx.filter_transactions(pg, user["id"])
    assert {(r["amount"], r["note"]) for r in rows} >= {(12000.0, "market")}
    new = auth.create_user(pg, "after_copy", PW, PW)           # ids continue after copied ones
    assert new > user["id"]
    with pytest.raises(SystemExit):                            # never copies twice
        copy(src_path, URL, really=True, out=lambda *_: None)
    pg.close()


# ---------------- the real app screens on PostgreSQL ----------------
@pytest.fixture
def app(monkeypatch):
    _wipe()
    monkeypatch.setattr(config, "database_url", lambda: URL)
    return AppTest.from_file("../app.py", default_timeout=60)


def _button(app, label):
    return next(b for b in app.button if b.label == label)


def test_app_sign_up_demo_edit_delete_all_pages(app):
    app.run()
    app.text_input[2].input("pg_app_user")
    app.text_input[3].input(PW)
    app.text_input[4].input(PW)
    _button(app, "Create account").click().run()
    assert not app.exception, app.exception
    _button(app, f"Add demo data ({tx.DEMO_EXPENSES} expenses + {tx.DEMO_INCOME} income)").click().run()
    assert not app.exception, app.exception
    _button(app, "Edit").click().run()
    assert app.title[0].value == "Edit transaction"
    app.text_input[0].set_value("edited on postgres")
    _button(app, "Save changes").click().run()
    assert any("Updated" in s.value for s in app.success), app.exception
    _button(app, "Delete").click().run()
    _button(app, "Yes, delete").click().run()
    assert any("Deleted" in s.value for s in app.success), app.exception
    for page in ["Overview", "Budgets", "Forecast", "Study Insights", "Add transaction",
                 "Import diary", "Transactions"]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, (page, app.exception)
    _button(app, "Log out").click().run()
    assert app.title[0].value == "Welcome to SmartCash"
