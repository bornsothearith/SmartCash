"""SCG-28 Daily USD/KHR exchange rates.

Source: National Bank of Cambodia (NBC) official rate, saved in
data/exchange_rates.csv. NBC publishes on working days only, so missing
days use the most recent earlier rate and are flagged as "filled".
"""
import bisect
import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from smartcash import config


@dataclass(frozen=True)
class RateUsed:
    khr_per_usd: float
    rate_date: date      # the day this rate was published
    filled: bool         # True = no rate that day, so an earlier day's rate is used


def read_rates_csv(path=None):
    """Return {date: (khr_per_usd, source)} from the CSV file."""
    path = path or config.RATES_CSV
    rates = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rate = float(row["khr_per_usd"])
            if rate <= 0:
                raise ValueError(f"Bad rate on {row['date']}: {rate}")
            rates[date.fromisoformat(row["date"])] = (rate, row["source"])
    if not rates:
        raise ValueError(f"No rates in {path}")
    return rates


_cache = {}


def _cached_rates():
    path = config.RATES_CSV
    key = (str(path), Path(path).stat().st_mtime)
    if key not in _cache:
        _cache.clear()
        _cache[key] = read_rates_csv(path)
    return _cache[key]


def rate_for(day, rates=None):
    """KHR per USD for `day`.

    - exact day in the table    -> that rate (filled=False)
    - day missing               -> most recent earlier rate (filled=True)
    - day before the first rate -> None
    """
    rates = _cached_rates() if rates is None else rates
    if day in rates:
        return RateUsed(rates[day][0], day, False)
    days = sorted(rates)
    i = bisect.bisect_left(days, day)
    if i == 0:
        return None
    earlier = days[i - 1]
    return RateUsed(rates[earlier][0], earlier, True)


def rate_used(day=None, rates=None):
    """Like rate_for, but never None: before the first date, use the first rate (filled)."""
    rates = _cached_rates() if rates is None else rates
    day = day or date.today()
    r = rate_for(day, rates)
    if r is None:
        first = min(rates)
        r = RateUsed(rates[first][0], first, True)
    return r


def sync_rates(conn, path=None):
    """Copy the CSV into the exchange_rates table with NO gaps.

    Every day from the first to the last date gets a row. Days with no
    published rate copy the day before and get is_filled = 1.
    """
    rates = read_rates_csv(path)
    first, last = min(rates), max(rates)
    rows, day = [], first
    while day <= last:
        r = rate_for(day, rates)
        rows.append((day.isoformat(), r.khr_per_usd, rates[r.rate_date][1], int(r.filled)))
        day += timedelta(days=1)
    # Skip the rewrite when the table already holds exactly these rates
    # (on PostgreSQL this saves ~70 network round trips at every start).
    have = {r["rate_date"]: (float(r["khr_per_usd"]), int(r["is_filled"]))
            for r in conn.execute("SELECT rate_date, khr_per_usd, is_filled FROM exchange_rates")}
    want = {d: (float(k), f) for d, k, _, f in rows}
    if have == want:
        return len(rows)
    conn.execute("DELETE FROM exchange_rates")
    conn.executemany(
        "INSERT INTO exchange_rates (rate_date, khr_per_usd, source, is_filled)"
        " VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    return len(rows)
