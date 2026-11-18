"""Sprint 3 acceptance gaps: SCG-30, SCG-32, SCG-34, plus the charts.

Uses temporary databases and fake data only.
"""
from datetime import date, timedelta

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from smartcash import auth, config, db, rates
from smartcash import transactions as tx
from smartcash.ui import charts

PW = "secret123"


@pytest.fixture
def conn(tmp_path):
    return db.connect(tmp_path / "gaps.db")


@pytest.fixture
def two_users(conn):
    return (auth.create_user(conn, "user_a", PW, PW),
            auth.create_user(conn, "user_b", PW, PW))


def income(**kw):
    base = dict(tx_date=date.today(), tx_type="income", amount=100, currency="USD",
                category="Allowance", payment_method="Cash", note="")
    base.update(kw)
    return tx.Transaction(**base)


# ---------------- SCG-30 Add income ----------------
@pytest.mark.parametrize("kw", [
    dict(amount=0), dict(amount=-5),                     # invalid amount
    dict(tx_date=date.today() + timedelta(days=1)),      # future date
    dict(category="Food & drinks"),                      # expense category on income
    dict(currency="KHR", amount=2500.5),                 # riel with decimals
])
def test_bad_income_is_rejected_and_not_saved(conn, two_users, kw):
    a, _ = two_users
    with pytest.raises(ValueError):
        tx.add_transaction(conn, a, income(**kw))
    assert tx.filter_transactions(conn, a) == []


@pytest.mark.parametrize("kind", tx.INCOME_CATEGORIES)
def test_every_income_type_is_accepted(conn, two_users, kind):
    a, _ = two_users
    tx.add_transaction(conn, a, income(category=kind))
    assert tx.filter_transactions(conn, a, tx_types=["income"])[0]["category"] == kind


# ---------------- SCG-32 Edit or delete ----------------
def test_user_cannot_edit_or_delete_someone_elses_row(conn, two_users):
    a, b = two_users
    row_id = tx.add_transaction(conn, a, income())
    with pytest.raises(ValueError):
        tx.update_transaction(conn, b, row_id, income(amount=999))
    with pytest.raises(ValueError):
        tx.delete_transaction(conn, b, row_id)
    assert tx.filter_transactions(conn, a)[0]["amount"] == 100


def test_edit_uses_same_checks_as_add(conn, two_users):
    a, _ = two_users
    row_id = tx.add_transaction(conn, a, income())
    with pytest.raises(ValueError):
        tx.update_transaction(conn, a, row_id, income(amount=0))
    assert tx.filter_transactions(conn, a)[0]["amount"] == 100


# ---------------- SCG-34 Dual currency ----------------
def test_weekend_uses_fridays_rate_and_is_flagged():
    saturday, friday = date(2026, 11, 14), date(2026, 11, 13)   # NBC has no Saturday rate
    r = rates.rate_used(saturday)
    assert r.filled and r.rate_date == friday
    assert tx.to_usd(8000, "KHR", saturday) == pytest.approx(8000 / r.khr_per_usd)
    assert tx.to_usd(8000, "KHR", saturday) == tx.to_usd(8000, "KHR", friday)


# ---------------- Charts ----------------
def _rows(*items):
    return [{"tx_date": d.isoformat(), "tx_type": t, "usd": u, "category": c}
            for d, t, u, c in items]


def test_weekly_totals_fill_empty_weeks_and_skip_current_week():
    today = date(2026, 11, 18)                      # Wednesday
    this_monday = date(2026, 11, 16)
    rows = _rows((this_monday - timedelta(days=7), "expense", 10, "Transport"),
                 (this_monday - timedelta(days=21), "expense", 5, "Transport"),
                 (this_monday, "expense", 7, "Transport"),          # current week
                 (this_monday - timedelta(days=7), "income", 50, "Allowance"))
    weekly, so_far = charts.weekly_totals(rows, weeks=4, today=today)
    assert list(weekly.usd) == [0.0, 5.0, 0.0, 10.0]   # 4 full weeks, gaps are 0, income ignored
    assert weekly.week_start.iloc[-1] == pd.Timestamp(this_monday - timedelta(days=7))
    assert so_far == 7.0


def test_forecast_is_average_and_range_of_last_4_weeks():
    weekly = pd.DataFrame({"usd": [99, 40, 50, 60, 70]})
    fc = charts.forecast(weekly)
    assert fc == {"estimate": 55.0, "low": 40.0, "high": 70.0, "weeks_used": 4}
    assert charts.forecast(pd.DataFrame({"usd": [0, 0]})) is None


def test_category_totals_biggest_first_expenses_only():
    rows = _rows((date(2026, 11, 2), "expense", 3, "Transport"),
                 (date(2026, 11, 2), "expense", 9, "Food & drinks"),
                 (date(2026, 11, 3), "income", 100, "Allowance"))
    cats = charts.category_totals(rows)
    assert list(cats.category) == ["Food & drinks", "Transport"]


def test_charts_have_titles_and_usd_axis():
    weekly, _ = charts.weekly_totals(_rows((date(2026, 11, 2), "expense", 3, "Transport")),
                                     weeks=4, today=date(2026, 11, 18))
    specs = [charts.weekly_spending_chart(weekly).to_dict(),
             charts.category_bars_chart(pd.DataFrame({"category": ["A"], "usd": [1.0]})).to_dict(),
             charts.forecast_chart(weekly, charts.forecast(weekly)).to_dict()]
    for spec in specs:
        assert spec["title"]["text"]
        assert "USD" in str(spec)


# ---------------- App screens (no browser) ----------------
@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "app.db")
    monkeypatch.setattr(config, "database_url", lambda: None)   # never touch a real database
    return AppTest.from_file("../app.py", default_timeout=30)


def _login(app, page="Transactions"):
    c = db.connect()
    uid = auth.create_user(c, "tester1", PW, PW)
    app.session_state["user"] = {"id": uid, "username": "tester1"}
    app.session_state["page"] = page
    return c, uid


def test_add_income_in_app_shows_in_list_and_totals(app):
    c, uid = _login(app, "Add transaction")
    app.run()
    next(r for r in app.radio if r.label == "Transaction type").set_value("income").run()
    app.number_input[0].set_value(60)
    next(b for b in app.button if b.label == "Save transaction").click().run()
    assert not app.exception
    rows = tx.filter_transactions(c, uid)
    assert rows[0]["tx_type"] == "income"
    app.session_state["page"] = "Transactions"
    app.run()
    html = " ".join(m.value for m in app.markdown)
    assert "Income" in html and "$60.00" in html


def test_delete_asks_first_and_names_the_row(app):
    c, uid = _login(app)
    row_id = tx.add_transaction(c, uid, income(amount=42))
    app.run()
    next(b for b in app.button if b.label == "Delete").click().run()
    assert any("42.00 USD" in w.value and "can't be undone" in w.value for w in app.warning)
    assert len(tx.filter_transactions(c, uid)) == 1          # not deleted yet
    next(b for b in app.button if b.label == "Cancel").click().run()
    assert len(tx.filter_transactions(c, uid)) == 1
    next(b for b in app.button if b.label == "Delete").click().run()
    next(b for b in app.button if b.label == "Yes, delete").click().run()
    assert tx.filter_transactions(c, uid) == []
    assert row_id


@pytest.mark.parametrize("page", ["Overview", "Forecast"])
def test_chart_pages_render_with_demo_data(app, page):
    c, uid = _login(app, page)
    tx.load_demo_data(c, uid, n=40)
    app.run()
    assert not app.exception
