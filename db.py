"""SmartCash data layer (Sprint 2).

Stores transactions in a local SQLite file for now. The table matches the
fields planned for the PostgreSQL schema (SCG-35), so it can move there later.
"""
import sqlite3
import csv
from dataclasses import dataclass
from datetime import date, timedelta
from io import TextIOBase
from pathlib import Path
import random

DB_PATH = Path(__file__).parent / "smartcash.db"

CURRENCIES = ["USD", "KHR"]
EXPENSE_CATEGORIES = [
    "Food & drinks", "Groceries", "Transport", "Phone & internet",
    "Education", "Rent & utilities", "Shopping & personal care",
    "Entertainment & social", "Health", "Family, gifts & ceremonies", "Other",
]
INCOME_CATEGORIES = ["Allowance", "Salary", "Scholarship", "Other income"]
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


@dataclass
class Transaction:
    tx_date: date
    tx_type: str
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
            participant_id TEXT DEFAULT '',
            is_demo INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(transactions)")}
    if "participant_id" not in columns:
        conn.execute("ALTER TABLE transactions ADD COLUMN participant_id TEXT DEFAULT ''")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS exchange_rates (
            rate_date TEXT PRIMARY KEY,
            khr_per_usd REAL NOT NULL CHECK (khr_per_usd > 0),
            source TEXT DEFAULT 'manual',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    if conn.execute("SELECT COUNT(*) FROM exchange_rates").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO exchange_rates (rate_date, khr_per_usd, source) VALUES (?, ?, ?)",
            (date.today().isoformat(), KHR_PER_USD, "Sprint 2 placeholder"),
        )
    conn.commit()
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


def validate_transaction(t: Transaction, today=None):
    """Return validation problems for income or expense records."""
    errors = []
    if t.tx_type not in ("expense", "income"):
        errors.append("Type must be expense or income.")
    if t.amount is None or t.amount <= 0:
        errors.append("Amount must be more than 0.")
    if t.currency not in CURRENCIES:
        errors.append("Currency must be USD or KHR.")
    elif t.currency == "KHR" and t.amount and t.amount != int(t.amount):
        errors.append("Riel amounts must be whole numbers.")
    allowed_categories = EXPENSE_CATEGORIES if t.tx_type == "expense" else INCOME_CATEGORIES
    if t.category not in allowed_categories:
        errors.append("Pick a valid category from the list.")
    if t.payment_method not in PAYMENT_METHODS:
        errors.append("Pick a payment method from the list.")
    today = today or date.today()
    if t.tx_date > today:
        errors.append("Date can't be in the future.")
    if len(t.note) > 200:
        errors.append("Note must be 200 characters or fewer.")
    return errors


def add_transaction(conn, t: Transaction, is_demo=False, participant_id=""):
    errors = validate_transaction(t)
    if errors:
        raise ValueError(" ".join(errors))
    cur = conn.execute(
        "INSERT INTO transactions (tx_date, tx_type, amount, currency, category, "
        "payment_method, note, participant_id, is_demo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (t.tx_date.isoformat(), t.tx_type, float(t.amount), t.currency,
         t.category, t.payment_method, t.note.strip(), participant_id.strip(), int(is_demo)),
    )
    conn.commit()
    return cur.lastrowid


def add_expense(conn, e: Expense, is_demo=False):
    return add_transaction(conn, Transaction(
        e.tx_date, "expense", e.amount, e.currency, e.category,
        e.payment_method, e.note
    ), is_demo=is_demo)


def set_exchange_rate(conn, rate_date, khr_per_usd, source="manual"):
    """Insert or update a daily KHR-per-USD rate."""
    if khr_per_usd <= 0:
        raise ValueError("Exchange rate must be more than 0.")
    value = rate_date.isoformat() if isinstance(rate_date, date) else str(rate_date)
    conn.execute(
        "INSERT INTO exchange_rates (rate_date, khr_per_usd, source) VALUES (?, ?, ?) "
        "ON CONFLICT(rate_date) DO UPDATE SET khr_per_usd=excluded.khr_per_usd, source=excluded.source",
        (value, float(khr_per_usd), source),
    )
    conn.commit()


def get_exchange_rate(conn, rate_date=None):
    """Return the latest rate on or before the requested date."""
    value = (rate_date or date.today()).isoformat()
    row = conn.execute(
        "SELECT khr_per_usd FROM exchange_rates WHERE rate_date <= ? "
        "ORDER BY rate_date DESC LIMIT 1", (value,)
    ).fetchone()
    return float(row[0]) if row else KHR_PER_USD


def to_usd(amount, currency, tx_date=None, conn=None):
    if currency == "USD":
        return amount
    rate = get_exchange_rate(conn, tx_date) if conn else KHR_PER_USD
    return amount / rate


def import_csv(conn, source, participant_id=""):
    """Import diary rows and return counts plus rejected-row reasons.

    Duplicate rows are skipped using the complete transaction fields. The
    participant ID is accepted for future PostgreSQL storage but is not stored
    in the Sprint 2 SQLite schema.
    """
    reader = csv.DictReader(source if hasattr(source, "read") else open(source, newline="", encoding="utf-8"))
    required = {"tx_date", "tx_type", "amount", "currency", "category", "payment_method"}
    missing = required - set(reader.fieldnames or [])
    if missing:
        raise ValueError("Missing CSV columns: " + ", ".join(sorted(missing)))
    existing = {
        (r["participant_id"] or "", r["tx_date"], r["tx_type"], r["amount"], r["currency"],
         r["category"], r["payment_method"], r["note"] or "")
        for r in conn.execute("SELECT participant_id, tx_date, tx_type, amount, currency, category, payment_method, note FROM transactions")
    }
    imported, duplicates, rejected = 0, 0, []
    for number, row in enumerate(reader, start=2):
        try:
            tx_date = date.fromisoformat(row["tx_date"].strip())
            tx = Transaction(
                tx_date=tx_date,
                tx_type=row["tx_type"].strip().lower(),
                amount=float(row["amount"]),
                currency=row["currency"].strip(),
                category=row["category"].strip(),
                payment_method=row["payment_method"].strip(),
                note=(row.get("note") or "").strip(),
            )
            key = (participant_id, tx.tx_date.isoformat(), tx.tx_type, str(tx.amount), tx.currency,
                   tx.category, tx.payment_method, tx.note)
            if key in existing or any(
                key[:3] == old[:3] and float(key[3]) == float(old[3]) and key[4:] == old[4:]
                for old in existing
            ):
                duplicates += 1
                continue
            errors = validate_transaction(tx)
            if errors:
                raise ValueError(" ".join(errors))
            add_transaction(conn, tx, is_demo=(row.get("is_demo", "0").strip() == "1"),
                            participant_id=participant_id)
            existing.add(key)
            imported += 1
        except Exception as exc:
            rejected.append({"row": number, "reason": str(exc)})
    return {"imported": imported, "duplicates": duplicates, "rejected": rejected}


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
