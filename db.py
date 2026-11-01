"""SmartCash data layer (Sprint 1).

Stores transactions in a local SQLite file for now. The table matches the
fields planned for the PostgreSQL schema (SCG-35), so it can move there later.
"""
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import random

DB_PATH = Path(__file__).parent / "smartcash.db"

CURRENCIES = ["USD", "KHR"]
EXPENSE_CATEGORIES = [
    "Food & drinks", "Groceries", "Transport", "Phone & internet",
    "Education", "Rent & utilities", "Shopping & personal care",
    "Entertainment & social", "Health", "Family, gifts & ceremonies", "Other",
]
PAYMENT_METHODS = ["Cash", "Mobile banking / QR", "Card", "Other"]

# Placeholder only. SCG-28 replaces this with a daily official rate table.
KHR_PER_USD = 4100


@dataclass
class Expense:
    tx_date: date
    amount: float
    currency: str
    category: str
    payment_method: str
    note: str = ""


def connect(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_date TEXT NOT NULL,
            tx_type TEXT NOT NULL CHECK (tx_type IN ('expense', 'income')),
            amount REAL NOT NULL CHECK (amount > 0),
            currency TEXT NOT NULL CHECK (currency IN ('USD', 'KHR')),
            category TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            note TEXT DEFAULT '',
            is_demo INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def validate_expense(e: Expense, today=None):
    """Return a list of problems. Empty list means the expense is valid."""
    today = today or date.today()
    errors = []
    if e.amount is None or e.amount <= 0:
        errors.append("Amount must be more than 0.")
    if e.currency not in CURRENCIES:
        errors.append("Currency must be USD or KHR.")
    elif e.currency == "KHR" and e.amount and e.amount != int(e.amount):
        errors.append("Riel amounts must be whole numbers.")
    if e.category not in EXPENSE_CATEGORIES:
        errors.append("Pick a category from the list.")
    if e.payment_method not in PAYMENT_METHODS:
        errors.append("Pick a payment method from the list.")
    if e.tx_date > today:
        errors.append("Date can't be in the future.")
    if len(e.note) > 200:
        errors.append("Note must be 200 characters or fewer.")
    return errors


def add_expense(conn, e: Expense, is_demo=False):
    errors = validate_expense(e)
    if errors:
        raise ValueError(" ".join(errors))
    cur = conn.execute(
        "INSERT INTO transactions (tx_date, tx_type, amount, currency, category,"
        " payment_method, note, is_demo) VALUES (?, 'expense', ?, ?, ?, ?, ?, ?)",
        (e.tx_date.isoformat(), float(e.amount), e.currency, e.category,
         e.payment_method, e.note.strip(), int(is_demo)),
    )
    conn.commit()
    return cur.lastrowid


def to_usd(amount, currency):
    return amount if currency == "USD" else amount / KHR_PER_USD


def filter_transactions(conn, start=None, end=None, categories=None, tx_types=None):
    """Return matching rows, newest first. Empty/None filters mean 'all'."""
    sql = "SELECT * FROM transactions WHERE 1=1"
    params = []
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


def load_demo_data(conn, n=30, seed=7):
    """Add clearly fake expenses so the list and filters can be demoed."""
    rng = random.Random(seed)
    today = date.today()
    for _ in range(n):
        cur = rng.choice(CURRENCIES)
        amt = rng.choice([1.5, 2.25, 3, 4.5, 8, 12]) if cur == "USD" else rng.choice([2000, 5000, 8000, 12000, 20000])
        add_expense(conn, Expense(
            tx_date=today - timedelta(days=rng.randint(0, 27)),
            amount=amt, currency=cur,
            category=rng.choice(EXPENSE_CATEGORIES),
            payment_method=rng.choice(PAYMENT_METHODS),
            note="demo",
        ), is_demo=True)


def clear_demo_data(conn):
    conn.execute("DELETE FROM transactions WHERE is_demo = 1")
    conn.commit()
