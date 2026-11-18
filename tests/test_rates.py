"""SCG-28 USD/KHR exchange-rate table."""
from datetime import date, timedelta

import pytest

from smartcash import db, rates
from smartcash import transactions as tx

# Small fake table so the tests don't depend on the real CSV numbers.
FAKE = {
    date(2026, 11, 2): (4080.0, "test"),
    date(2026, 11, 3): (4084.0, "test"),
    date(2026, 11, 6): (4088.0, "test"),
}


def test_exact_day_uses_that_days_rate():
    r = rates.rate_for(date(2026, 11, 3), FAKE)
    assert r.khr_per_usd == 4084 and r.rate_date == date(2026, 11, 3) and not r.filled


def test_missing_day_uses_previous_day_and_is_flagged():
    r = rates.rate_for(date(2026, 11, 5), FAKE)  # no rate on the 4th or 5th
    assert r.khr_per_usd == 4084 and r.rate_date == date(2026, 11, 3) and r.filled


def test_no_rate_before_first_date():
    assert rates.rate_for(date(2026, 11, 1), FAKE) is None


def test_to_usd_uses_rate_of_the_transaction_day():
    rate = rates.rate_used(date(2026, 11, 3)).khr_per_usd  # real CSV
    assert tx.to_usd(8000, "KHR", date(2026, 11, 3)) == pytest.approx(8000 / rate)
    assert tx.to_usd(3.5, "USD", date(2026, 11, 3)) == 3.5


def test_real_csv_is_valid_and_covers_60_days():
    real = rates.read_rates_csv()
    assert (max(real) - min(real)).days >= 60
    assert all(3500 < r < 4500 for r, _ in real.values())  # sane KHR per USD
    assert all(src for _, src in real.values())


def test_rates_table_has_no_gaps(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    rows = conn.execute(
        "SELECT rate_date, is_filled FROM exchange_rates ORDER BY rate_date").fetchall()
    days = [date.fromisoformat(r["rate_date"]) for r in rows]
    assert days[0] == min(rates.read_rates_csv())
    assert all(b - a == timedelta(days=1) for a, b in zip(days, days[1:]))
    # weekends have no official rate, so some rows must be flagged as filled
    assert any(r["is_filled"] for r in rows)
