"""Checks the acceptance criteria for SCG-31 and SCG-33."""
from datetime import date, timedelta
import sqlite3
import pytest
import db


@pytest.fixture
def conn(tmp_path):
    return db.connect(tmp_path / "test.db")


def good(**kw):
    base = dict(tx_date=date.today(), amount=3.5, currency="USD",
                category="Food & drinks", payment_method="Cash", note="")
    base.update(kw)
    return db.Expense(**base)


# SCG-31: all fields validated
@pytest.mark.parametrize("kw", [
    dict(amount=0), dict(amount=-2), dict(currency="EUR"),
    dict(currency="KHR", amount=2500.5), dict(category="Pizza"),
    dict(payment_method="Bitcoin"), dict(tx_date=date.today() + timedelta(days=1)),
    dict(note="x" * 201),
])
def test_bad_expenses_are_rejected(conn, kw):
    assert db.validate_expense(good(**kw))
    with pytest.raises(ValueError):
        db.add_expense(conn, good(**kw))


# SCG-31: saved to the database and appears in the list
def test_valid_expense_is_saved_and_listed(conn):
    db.add_expense(conn, good(amount=12000, currency="KHR"))
    rows = db.filter_transactions(conn)
    assert len(rows) == 1 and rows[0]["amount"] == 12000 and rows[0]["currency"] == "KHR"


# SCG-33: filters combine correctly and match a direct SQL check
def test_filters_match_sql(conn):
    db.load_demo_data(conn, n=50)
    start, end = date.today() - timedelta(days=10), date.today()
    cats = ["Food & drinks", "Transport"]
    got = db.filter_transactions(conn, start, end, cats, ["expense"])
    expected = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE tx_date BETWEEN ? AND ? "
        "AND category IN (?, ?) AND tx_type = 'expense'",
        (start.isoformat(), end.isoformat(), *cats)).fetchone()[0]
    assert len(got) == expected
    assert all(r["category"] in cats and start.isoformat() <= r["tx_date"] <= end.isoformat() for r in got)


def test_no_filters_returns_everything(conn):
    db.load_demo_data(conn, n=20)
    assert len(db.filter_transactions(conn)) == 20


def test_demo_data_can_be_removed(conn):
    db.add_expense(conn, good())
    db.load_demo_data(conn, n=10)
    db.clear_demo_data(conn)
    assert len(db.filter_transactions(conn)) == 1
