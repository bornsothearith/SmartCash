"""Checks the acceptance criteria for SCG-30 Add income (subtask SCG-119)."""
from datetime import date, timedelta
import pytest
import db


@pytest.fixture
def conn(tmp_path):
    return db.connect(tmp_path / "test.db")


def good(**kw):
    base = dict(tx_date=date.today(), amount=60, currency="USD",
                income_type="Allowance", received_as="", note="")
    base.update(kw)
    return db.Income(**base)


# Valid save: stored as income, with the type in category, and listed as income
@pytest.mark.parametrize("received", ["", "Mobile banking / QR"])
def test_valid_income_is_saved_and_listed(conn, received):
    db.add_income(conn, good(amount=100000, currency="KHR", income_type="Part-time job",
                             received_as=received))
    rows = db.filter_transactions(conn)
    assert len(rows) == 1
    r = rows[0]
    assert (r["tx_type"], r["amount"], r["currency"], r["category"], r["payment_method"]) == \
        ("income", 100000, "KHR", "Part-time job", received)


@pytest.mark.parametrize("kind", db.INCOME_TYPES)
def test_every_income_type_is_accepted(kind):
    assert db.validate_income(good(income_type=kind)) == []


# Invalid fields: each one is rejected with a clear message and nothing is saved
@pytest.mark.parametrize("kw, message", [
    (dict(amount=0), "Amount must be more than 0."),
    (dict(amount=-5), "Amount must be more than 0."),
    (dict(currency="EUR"), "Currency must be USD or KHR."),
    (dict(currency="KHR", amount=2500.5), "Riel amounts must be whole numbers."),
    (dict(income_type="Lottery"), "Pick an income type from the list."),
    (dict(received_as="Bitcoin"), "Pick how you received it from the list, or leave it blank."),
    (dict(tx_date=date.today() + timedelta(days=1)), "Date can't be in the future."),
    (dict(note="x" * 201), "Note must be 200 characters or fewer."),
])
def test_bad_income_is_rejected(conn, kw, message):
    assert message in db.validate_income(good(**kw))
    with pytest.raises(ValueError):
        db.add_income(conn, good(**kw))
    assert db.filter_transactions(conn) == []


# Income filter returns income only
def test_income_filter(conn):
    db.load_demo_data(conn, n=10)
    db.add_income(conn, good())
    got = db.filter_transactions(conn, tx_types=["income"])
    assert len(got) == 1 and got[0]["tx_type"] == "income"
    assert len(db.filter_transactions(conn, tx_types=["expense"])) == 10


# Totals: Income, Spending and Net are separate and match a direct SQL check
def test_totals_are_separate(conn):
    db.add_income(conn, good(amount=100))
    db.add_income(conn, good(amount=41000, currency="KHR"))        # $10 at 4,100
    db.add_expense(conn, db.Expense(date.today(), 25.5, "USD", "Food & drinks", "Cash"))
    db.add_expense(conn, db.Expense(date.today(), 8200, "KHR", "Transport", "Cash"))  # $2
    s = db.summarize(db.filter_transactions(conn))
    assert (s["income"], s["spending"], s["net"]) == (110.0, 27.5, 82.5)
    assert (s["income_count"], s["expense_count"], s["count"]) == (2, 2, 4)


def test_totals_match_sql(conn):
    db.load_demo_data(conn, n=30)
    db.load_demo_income(conn)
    s = db.summarize(db.filter_transactions(conn))
    usd = "SUM(CASE WHEN currency='USD' THEN amount ELSE amount / ? END)"
    income, spending = (conn.execute(f"SELECT {usd} FROM transactions WHERE tx_type=?",
                                     (db.KHR_PER_USD, t)).fetchone()[0]
                        for t in ("income", "expense"))
    assert s["income"] == pytest.approx(income, abs=0.01)
    assert s["spending"] == pytest.approx(spending, abs=0.01)
    assert s["net"] == pytest.approx(income - spending, abs=0.01)


def test_demo_income_is_labelled_and_removable(conn):
    db.add_income(conn, good())
    db.load_demo_income(conn)
    assert all(r["is_demo"] == 1 for r in db.filter_transactions(conn) if r["note"] == "demo")
    db.clear_demo_data(conn)
    assert len(db.filter_transactions(conn)) == 1
