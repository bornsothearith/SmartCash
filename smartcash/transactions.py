"""SCG-31 Add expense and SCG-33 View and filter transactions.

Every function takes a user_id, so a user only ever reads or changes
their own rows (SCG-75).
"""
import random
from dataclasses import dataclass
from datetime import date, timedelta

from smartcash import rates
from smartcash.validation import (
    CURRENCIES,
    EXPENSE_CATEGORIES,
    PAYMENT_METHODS,
    validate_expense,
)


@dataclass
class Expense:
    tx_date: date
    amount: float
    currency: str
    category: str
    payment_method: str
    note: str = ""


def add_expense(conn, user_id, e: Expense, is_demo=False):
    if not user_id:
        raise ValueError("You must be logged in.")
    errors = validate_expense(e)
    if errors:
        raise ValueError(" ".join(errors))
    cur = conn.execute(
        "INSERT INTO transactions (user_id, tx_date, tx_type, amount, currency, category,"
        " payment_method, note, is_demo) VALUES (?, ?, 'expense', ?, ?, ?, ?, ?, ?)",
        (user_id, e.tx_date.isoformat(), float(e.amount), e.currency, e.category,
         e.payment_method, e.note.strip(), int(is_demo)),
    )
    conn.commit()
    return cur.lastrowid


def to_usd(amount, currency, tx_date=None):
    """Convert to USD with the official rate of the transaction's day (SCG-28)."""
    if currency == "USD":
        return amount
    if isinstance(tx_date, str):
        tx_date = date.fromisoformat(tx_date)
    return amount / rates.rate_used(tx_date).khr_per_usd


def filter_transactions(conn, user_id, start=None, end=None, categories=None, tx_types=None):
    """Return this user's matching rows, newest first. Empty/None filters mean 'all'."""
    sql = "SELECT * FROM transactions WHERE user_id = ?"
    params = [user_id]
    if start:
        sql += " AND tx_date >= ?"
        params.append(start.isoformat())
    if end:
        sql += " AND tx_date <= ?"
        params.append(end.isoformat())
    if categories:
        sql += f" AND category IN ({','.join('?' * len(categories))})"
        params += list(categories)
    if tx_types:
        sql += f" AND tx_type IN ({','.join('?' * len(tx_types))})"
        params += list(tx_types)
    sql += " ORDER BY tx_date DESC, id DESC"
    return [dict(r) for r in conn.execute(sql, params)]


def load_demo_data(conn, user_id, n=30, seed=7):
    """Add clearly fake expenses so the list and filters can be demoed."""
    rng = random.Random(seed)
    today = date.today()
    for _ in range(n):
        cur = rng.choice(CURRENCIES)
        amt = (rng.choice([1.5, 2.25, 3, 4.5, 8, 12]) if cur == "USD"
               else rng.choice([2000, 5000, 8000, 12000, 20000]))
        add_expense(conn, user_id, Expense(
            tx_date=today - timedelta(days=rng.randint(0, 27)),
            amount=amt, currency=cur,
            category=rng.choice(EXPENSE_CATEGORIES),
            payment_method=rng.choice(PAYMENT_METHODS),
            note="demo",
        ), is_demo=True)


def clear_demo_data(conn, user_id):
    conn.execute("DELETE FROM transactions WHERE is_demo = 1 AND user_id = ?", (user_id,))
    conn.commit()
