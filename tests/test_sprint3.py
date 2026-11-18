"""Acceptance checks for Sprint 3 transaction management and diary imports."""

import sqlite3
from datetime import date
from io import StringIO

from smartcash import db, diary_import
from smartcash import transactions as tx


def _conn(tmp_path):
    conn = db.connect(tmp_path / "sprint3.db")
    user_id = 1
    conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                 ("sprint3", "test-hash"))
    conn.commit()
    return conn, user_id


def test_income_edit_and_delete_are_supported(tmp_path):
    conn, user_id = _conn(tmp_path)
    income = tx.Transaction(date.today(), "income", 250, "USD", "Allowance", "Cash")
    transaction_id = tx.add_transaction(conn, user_id, income)
    assert tx.filter_transactions(conn, user_id)[0]["tx_type"] == "income"

    updated = tx.Transaction(date.today(), "income", 300, "USD", "Scholarship", "Card")
    tx.update_transaction(conn, user_id, transaction_id, updated)
    row = tx.filter_transactions(conn, user_id)[0]
    assert row["amount"] == 300 and row["category"] == "Scholarship"

    tx.delete_transaction(conn, user_id, transaction_id)
    assert tx.filter_transactions(conn, user_id) == []


def test_diary_import_reports_imports_duplicates_and_rejections(tmp_path):
    conn, user_id = _conn(tmp_path)
    csv_data = StringIO(
        "tx_date,tx_type,amount,currency,category,payment_method,note,is_demo\n"
        "2026-11-01,income,100,USD,Allowance,Cash,weekly,0\n"
        "2026-11-01,income,100,USD,Allowance,Cash,weekly,0\n"
        "2026-11-01,income,0,USD,Allowance,Cash,bad,0\n"
    )
    result = diary_import.import_csv(conn, user_id, csv_data)
    assert result["imported"] == 1
    assert result["duplicates"] == 1
    assert len(result["rejected"]) == 1


def test_old_exchange_rate_table_is_migrated(tmp_path):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.execute("CREATE TABLE exchange_rates (rate_date TEXT PRIMARY KEY, khr_per_usd REAL NOT NULL, source TEXT NOT NULL)")
    old.commit()
    old.close()

    conn = db.connect(path)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(exchange_rates)")}
    assert {"source", "is_filled"} <= columns
