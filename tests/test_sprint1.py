"""Checks the acceptance criteria for SCG-31 and SCG-33."""
from datetime import date, timedelta

import pytest

from smartcash import auth, db
from smartcash import transactions as tx


@pytest.fixture
def conn(tmp_path):
    return db.connect(tmp_path / "test.db")


@pytest.fixture
def uid(conn):
    return auth.create_user(conn, "tester1", "secret123", "secret123")


def good(**kw):
    base = dict(tx_date=date.today(), amount=3.5, currency="USD",
                category="Food & drinks", payment_method="Cash", note="")
    base.update(kw)
    return tx.Expense(**base)


# SCG-31: all fields validated
@pytest.mark.parametrize("kw", [
    dict(amount=0), dict(amount=-2), dict(currency="EUR"),
    dict(currency="KHR", amount=2500.5), dict(category="Pizza"),
    dict(payment_method="Bitcoin"), dict(tx_date=date.today() + timedelta(days=1)),
    dict(note="x" * 201),
])
def test_bad_expenses_are_rejected(conn, uid, kw):
    assert tx.validate_expense(good(**kw))
    with pytest.raises(ValueError):
        tx.add_expense(conn, uid, good(**kw))


# SCG-31: saved to the database and appears in the list
def test_valid_expense_is_saved_and_listed(conn, uid):
    tx.add_expense(conn, uid, good(amount=12000, currency="KHR"))
    rows = tx.filter_transactions(conn, uid)
    assert len(rows) == 1 and rows[0]["amount"] == 12000 and rows[0]["currency"] == "KHR"


# SCG-33: filters combine correctly and match a direct SQL check
def test_filters_match_sql(conn, uid):
    tx.load_demo_data(conn, uid, n=50)
    start, end = date.today() - timedelta(days=10), date.today()
    cats = ["Food & drinks", "Transport"]
    got = tx.filter_transactions(conn, uid, start, end, cats, ["expense"])
    expected = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE user_id = ? AND tx_date BETWEEN ? AND ? "
        "AND category IN (?, ?) AND tx_type = 'expense'",
        (uid, start.isoformat(), end.isoformat(), *cats)).fetchone()[0]
    assert len(got) == expected
    assert all(r["category"] in cats and start.isoformat() <= r["tx_date"] <= end.isoformat() for r in got)


def test_no_filters_returns_everything(conn, uid):
    tx.load_demo_data(conn, uid, n=20)
    assert len(tx.filter_transactions(conn, uid)) == 20


def test_demo_data_can_be_removed(conn, uid):
    tx.add_expense(conn, uid, good())
    tx.load_demo_data(conn, uid, n=10)
    tx.clear_demo_data(conn, uid)
    assert len(tx.filter_transactions(conn, uid)) == 1
