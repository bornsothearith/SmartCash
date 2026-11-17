"""Acceptance checks for Sprint 2 exchange rates and diary imports."""
from datetime import date
from io import StringIO

import db


def test_daily_exchange_rate_is_used(tmp_path):
    conn = db.connect(tmp_path / "rates.db")
    db.set_exchange_rate(conn, date(2026, 11, 1), 4100, "test")
    db.set_exchange_rate(conn, date(2026, 11, 2), 4200, "test")
    assert db.to_usd(8400, "KHR", date(2026, 11, 2), conn) == 2
    assert db.to_usd(8400, "KHR", date(2026, 11, 3), conn) == 2


def test_csv_import_reports_duplicates_and_bad_rows(tmp_path):
    conn = db.connect(tmp_path / "import.db")
    csv_data = StringIO(
        "tx_date,tx_type,amount,currency,category,payment_method,note,is_demo\n"
        "2026-11-01,expense,3.50,USD,Food & drinks,Cash,lunch,1\n"
        "2026-11-01,expense,3.50,USD,Food & drinks,Cash,lunch,1\n"
        "2026-11-01,expense,0,USD,Food & drinks,Cash,bad,1\n"
    )
    result = db.import_csv(conn, csv_data)
    assert result["imported"] == 1
    assert result["duplicates"] == 1
    assert len(result["rejected"]) == 1
