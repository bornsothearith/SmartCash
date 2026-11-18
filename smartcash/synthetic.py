"""SCG-29 Synthetic test data.

Makes FAKE transactions for tests and demos, before real diary data grows.
  - normal rows: realistic student expenses and income in USD and KHR
  - messy rows:  broken on purpose (bad amount, future date, ...) so we can
                 check that validation rejects them

Never use this data for findings or statistics. Every row is marked
source="synthetic".

Run:  python -m smartcash.synthetic      -> writes data/synthetic/sample.csv
      python -m smartcash.synthetic --normal 200 --messy 30 --out my_file.csv
"""
import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from smartcash import transactions as tx

INCOME_CATEGORIES = ["Allowance", "Part-time job", "Scholarship", "Gift", "Other"]

FIELDS = ["tx_date", "tx_type", "amount", "currency", "category",
          "payment_method", "note", "source", "problem"]

# Typical prices a student pays, per category: (USD choices, KHR choices).
_PRICES = {
    "Food & drinks": ([1.5, 2, 2.5, 3, 4.5], [3000, 5000, 6000, 8000, 10000]),
    "Groceries": ([3, 5, 8, 12], [10000, 15000, 25000, 40000]),
    "Transport": ([1, 1.5, 2, 3], [2000, 4000, 6000, 8000]),
    "Phone & internet": ([1, 2, 5], [4000, 8000, 20000]),
    "Education": ([2, 5, 10, 25], [2000, 5000, 10000]),
    "Rent & utilities": ([40, 60, 80, 100], [100000, 200000]),
    "Shopping & personal care": ([3, 6, 10, 15], [8000, 15000, 30000]),
    "Entertainment & social": ([2, 4, 6, 10], [8000, 15000, 25000]),
    "Health": ([2, 5, 10], [5000, 10000, 20000]),
    "Family, gifts & ceremonies": ([5, 10, 20, 50], [20000, 50000, 100000]),
    "Other": ([1, 2, 5], [2000, 5000, 10000]),
}
_INCOME = {
    "Allowance": ([100, 150, 200, 250], [400000, 600000, 800000]),
    "Part-time job": ([30, 50, 80], [100000, 200000]),
    "Scholarship": ([100, 200], [400000]),
    "Gift": ([10, 20, 50], [20000, 50000, 100000]),
    "Other": ([5, 10], [20000, 40000]),
}


def _row(tx_date, tx_type, amount, currency, category, payment, note="", problem=""):
    return {"tx_date": tx_date, "tx_type": tx_type, "amount": amount,
            "currency": currency, "category": category, "payment_method": payment,
            "note": note, "source": "synthetic", "problem": problem}


def normal_rows(n=100, seed=7, days=56, today=None):
    """Valid rows over the last `days` days. About 1 in 10 is income."""
    rng = random.Random(seed)
    today = today or date.today()
    rows = []
    for _ in range(n):
        d = today - timedelta(days=rng.randint(0, days - 1))
        cur = rng.choice(tx.CURRENCIES)
        if rng.random() < 0.1:
            cat = rng.choice(INCOME_CATEGORIES)
            usd, khr = _INCOME[cat]
            rows.append(_row(d, "income", rng.choice(usd if cur == "USD" else khr),
                             cur, cat, rng.choice(["Cash", "Mobile banking / QR"])))
        else:
            cat = rng.choice(tx.EXPENSE_CATEGORIES)
            usd, khr = _PRICES[cat]
            rows.append(_row(d, "expense", rng.choice(usd if cur == "USD" else khr),
                             cur, cat, rng.choice(tx.PAYMENT_METHODS)))
    return rows


# Each messy kind breaks exactly one rule. Value = function that changes a good row.
MESSY_KINDS = {
    "zero_amount": lambda r, t: r.update(amount=0),
    "negative_amount": lambda r, t: r.update(amount=-5),
    "future_date": lambda r, t: r.update(tx_date=t + timedelta(days=3)),
    "unknown_currency": lambda r, t: r.update(currency="EUR"),
    "lowercase_currency": lambda r, t: r.update(currency="usd"),
    "riel_with_decimals": lambda r, t: r.update(currency="KHR", amount=2500.5),
    "unknown_category": lambda r, t: r.update(category="Pizza"),
    "unknown_payment": lambda r, t: r.update(payment_method="Bitcoin"),
    "note_too_long": lambda r, t: r.update(note="x" * 201),
}


def messy_rows(n=20, seed=11, today=None):
    """Broken expense rows. `problem` says what is wrong with each one.

    Also adds exact duplicates (problem="duplicate"): they pass validation,
    but a duplicate-safe import (later sprint) must skip them.
    """
    rng = random.Random(seed)
    today = today or date.today()
    base = normal_rows(n, seed=seed, today=today)
    base = [r for r in base if r["tx_type"] == "expense"]
    kinds = list(MESSY_KINDS) + ["duplicate"]
    rows = []
    for i, r in enumerate(base):
        kind = kinds[i % len(kinds)]  # cycle so every kind appears
        if kind == "duplicate":
            rows += [dict(r, problem="duplicate"), dict(r, problem="duplicate")]
        else:
            r = dict(r, problem=kind)
            MESSY_KINDS[kind](r, today)
            rows.append(r)
    rng.shuffle(rows)
    return rows


def to_expense(row):
    """Turn an expense row into a tx.Expense so it can be validated or saved."""
    return tx.Expense(row["tx_date"], row["amount"], row["currency"],
                      row["category"], row["payment_method"], row["note"])


def write_csv(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(dict(r, tx_date=r["tx_date"].isoformat()))
    return path


def main():
    p = argparse.ArgumentParser(description="Make fake SmartCash test data.")
    p.add_argument("--normal", type=int, default=100)
    p.add_argument("--messy", type=int, default=20)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--out", default="data/synthetic/sample.csv")
    a = p.parse_args()
    rows = normal_rows(a.normal, seed=a.seed) + messy_rows(a.messy, seed=a.seed + 1)
    out = write_csv(rows, a.out)
    bad = sum(1 for r in rows if r["problem"])
    print(f"Wrote {len(rows)} fake rows ({bad} messy) to {out}")


if __name__ == "__main__":
    main()
