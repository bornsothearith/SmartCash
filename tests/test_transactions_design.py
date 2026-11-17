"""Transactions tab on the design system: separate totals and on-system formatting."""
from datetime import date
import pytest
import db
import ui


@pytest.fixture
def conn(tmp_path):
    return db.connect(tmp_path / "test.db")


def add_income(conn, amount, currency):
    # No add_income yet (SCG-30), so insert an income row directly.
    conn.execute("INSERT INTO transactions (tx_date, tx_type, amount, currency, category,"
                 " payment_method) VALUES (?, 'income', ?, ?, 'Allowance', 'Cash')",
                 (date.today().isoformat(), amount, currency))
    conn.commit()


def test_summary_keeps_income_spending_and_net_apart(conn):
    add_income(conn, 100, "USD")
    add_income(conn, 41000, "KHR")  # $10 at the placeholder rate
    db.add_expense(conn, db.Expense(date.today(), 25.5, "USD", "Food & drinks", "Cash"))
    db.add_expense(conn, db.Expense(date.today(), 8200, "KHR", "Transport", "Cash"))  # $2
    s = db.summarize(db.filter_transactions(conn))
    assert s == {"count": 4, "income_count": 2, "expense_count": 2,
                 "income": 110.0, "spending": 27.5, "net": 82.5}


def test_summary_matches_sql(conn):
    db.load_demo_data(conn, n=40)
    add_income(conn, 50, "USD")
    s = db.summarize(db.filter_transactions(conn))
    usd = "SUM(CASE WHEN currency='USD' THEN amount ELSE amount / ? END)"
    spent = conn.execute(f"SELECT {usd} FROM transactions WHERE tx_type='expense'",
                         (db.KHR_PER_USD,)).fetchone()[0]
    assert s["spending"] == pytest.approx(spent, abs=0.01)
    assert s["net"] == pytest.approx(50 - spent, abs=0.01)


def test_empty_summary_is_zero():
    assert db.summarize([]) == {"count": 0, "income_count": 0, "expense_count": 0,
                                "income": 0, "spending": 0, "net": 0}


@pytest.mark.parametrize("args, expected", [
    ((1284.5, "USD"), "$1,284.50"),
    ((40000, "KHR"), "៛40,000"),
    ((3, "USD", "+"), "+$3.00"),
    ((12000, "KHR", "-"), "−៛12,000"),
    ((-7.25, "USD"), "−$7.25"),
])
def test_money_format(args, expected):
    assert ui.format_money(*args) == expected


def test_amounts_always_carry_a_sign_not_only_colour():
    assert "+$5.00" in ui.amount_html(5, "USD", "income")
    assert "sc-amount--income" in ui.amount_html(5, "USD", "income")
    assert "−៛500" in ui.amount_html(500, "KHR", "expense")
    assert ui.net_direction(-1) == "expense" and ui.net_direction(0) is None


def test_table_escapes_user_text():
    row = dict(tx_date="2026-11-17", tx_type="expense", amount=2, currency="USD",
               category="Food & drinks", payment_method="Cash", note="<script>x</script>")
    out = ui.transactions_table([row])
    assert "<script>" not in out and "&lt;script&gt;" in out
    assert "Expense" in out and "Food &amp; drinks" in out
