"""Transaction operations for income, expenses, editing, and deletion.

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
    INCOME_CATEGORIES,
    PAYMENT_METHODS,
    validate_transaction,
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


@dataclass
class Transaction:
    tx_date: date
    tx_type: str
    amount: float
    currency: str
    category: str
    payment_method: str
    note: str = ""


def add_transaction(conn, user_id, transaction: Transaction, is_demo=False, *, commit=True):
    """Save an income or expense transaction for one user."""
    if not user_id:
        raise ValueError("You must be logged in.")
    errors = validate_transaction(transaction)
    if errors:
        raise ValueError(" ".join(errors))
    cur = conn.execute(
        "INSERT INTO transactions (user_id, tx_date, tx_type, amount, currency, category,"
        " payment_method, note, is_demo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
        (user_id, transaction.tx_date.isoformat(), transaction.tx_type,
         float(transaction.amount), transaction.currency, transaction.category,
         transaction.payment_method, transaction.note.strip(), int(is_demo)),
    )
    new_transaction = cur.fetchone()
    if commit:
        conn.commit()
    return (new_transaction["id"] if hasattr(new_transaction, "keys")
            else new_transaction[0])


def add_expense(conn, user_id, e: Expense, is_demo=False):
    return add_transaction(conn, user_id, Transaction(
        e.tx_date, "expense", e.amount, e.currency, e.category,
        e.payment_method, e.note), is_demo=is_demo)


def update_transaction(conn, user_id, transaction_id, transaction: Transaction):
    """Update one transaction, restricted to its owner."""
    if not user_id:
        raise ValueError("You must be logged in.")
    errors = validate_transaction(transaction)
    if errors:
        raise ValueError(" ".join(errors))
    cur = conn.execute(
        "UPDATE transactions SET tx_date = ?, tx_type = ?, amount = ?, currency = ?,"
        " category = ?, payment_method = ?, note = ? WHERE id = ? AND user_id = ?",
        (transaction.tx_date.isoformat(), transaction.tx_type, float(transaction.amount),
         transaction.currency, transaction.category, transaction.payment_method,
         transaction.note.strip(), transaction_id, user_id),
    )
    conn.commit()
    if cur.rowcount != 1:
        raise ValueError("Transaction was not found.")


def delete_transaction(conn, user_id, transaction_id):
    """Delete one transaction, restricted to its owner."""
    if not user_id:
        raise ValueError("You must be logged in.")
    cur = conn.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?",
                       (transaction_id, user_id))
    conn.commit()
    if cur.rowcount != 1:
        raise ValueError("Transaction was not found.")


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


# How much demo data the sidebar button adds, spread over 8 weeks so every chart has data.
DEMO_EXPENSES = 60
DEMO_INCOME = 45
DEMO_DAYS = 56


def load_demo_data(conn, user_id, n=30, seed=7, days=28, today=None):
    """Add clearly fake expenses so the list and filters can be demoed."""
    rng = random.Random(seed)
    today = today or date.today()
    for _ in range(n):
        cur = rng.choice(CURRENCIES)
        amt = (rng.choice([1.5, 2.25, 3, 4.5, 8, 12]) if cur == "USD"
               else rng.choice([2000, 5000, 8000, 12000, 20000]))
        add_expense(conn, user_id, Expense(
            tx_date=today - timedelta(days=rng.randint(0, days - 1)),
            amount=amt, currency=cur,
            category=rng.choice(EXPENSE_CATEGORIES),
            payment_method=rng.choice(PAYMENT_METHODS),
            note="demo",
        ), is_demo=True)
    return n


def load_demo_income(conn, user_id, n=DEMO_INCOME, seed=11, days=DEMO_DAYS, today=None):
    """Add clearly fake student income: weekly allowance, part-time shifts, gifts.

    - one $25 allowance every week
    - one $100 scholarship payment
    - the rest: part-time job shifts (most) and small gifts, in USD or KHR
    """
    rng = random.Random(seed)
    today = today or date.today()
    rows = [("Allowance", 25, "USD", d, "Cash") for d in range(0, days, 7)]
    rows.append(("Scholarship", 100, "USD", min(40, days - 1), "Mobile banking / QR"))
    while len(rows) < n:
        cur = rng.choice(CURRENCIES)
        if rng.random() < 0.75:
            kind = "Part-time job"
            amt = rng.choice([5, 8, 10]) if cur == "USD" else rng.choice([20000, 30000, 40000])
        else:
            kind = "Gift"
            amt = rng.choice([5, 10]) if cur == "USD" else rng.choice([10000, 20000])
        rows.append((kind, amt, cur, rng.randint(0, days - 1),
                     rng.choice(["Cash", "Mobile banking / QR"])))
    for kind, amount, currency, days_ago, received in rows[:n]:
        add_transaction(conn, user_id, Transaction(
            today - timedelta(days=days_ago), "income", amount, currency,
            kind, received, "demo"), is_demo=True)
    return min(n, len(rows))


def clear_demo_data(conn, user_id):
    conn.execute("DELETE FROM transactions WHERE is_demo = 1 AND user_id = ?", (user_id,))
    conn.commit()
