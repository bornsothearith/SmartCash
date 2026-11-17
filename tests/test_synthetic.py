"""Checks the acceptance criteria for SCG-29 Synthetic test data."""
import csv
from datetime import date

from smartcash import synthetic
from smartcash import transactions as tx


def test_normal_rows_are_valid_and_marked_fake():
    rows = synthetic.normal_rows(200)
    assert len(rows) == 200
    assert all(r["source"] == "synthetic" and r["problem"] == "" for r in rows)
    expenses = [r for r in rows if r["tx_type"] == "expense"]
    assert all(not tx.validate_expense(synthetic.to_expense(r)) for r in expenses)


def test_normal_rows_have_both_currencies_and_income():
    rows = synthetic.normal_rows(200)
    assert {r["currency"] for r in rows} == {"USD", "KHR"}
    income = [r for r in rows if r["tx_type"] == "income"]
    assert income and all(r["category"] in synthetic.INCOME_CATEGORIES for r in income)
    assert all(r["amount"] > 0 and r["tx_date"] <= date.today() for r in income)


def test_every_messy_kind_appears_and_is_rejected():
    rows = synthetic.messy_rows(40)
    kinds = {r["problem"] for r in rows}
    assert set(synthetic.MESSY_KINDS) | {"duplicate"} <= kinds
    for r in rows:
        if r["problem"] != "duplicate":
            assert tx.validate_expense(synthetic.to_expense(r)), r["problem"]


def test_duplicates_come_in_identical_pairs():
    dups = [r for r in synthetic.messy_rows(40) if r["problem"] == "duplicate"]
    assert dups and len(dups) % 2 == 0
    keys = [tuple(r.values()) for r in dups]
    assert all(keys.count(k) >= 2 for k in keys)


def test_same_seed_gives_same_data():
    assert synthetic.normal_rows(50, seed=3) == synthetic.normal_rows(50, seed=3)


def test_csv_round_trip(tmp_path):
    rows = synthetic.normal_rows(10) + synthetic.messy_rows(10)
    path = synthetic.write_csv(rows, tmp_path / "out.csv")
    with open(path, encoding="utf-8") as f:
        back = list(csv.DictReader(f))
    assert len(back) == len(rows)
    assert all(r["source"] == "synthetic" for r in back)
