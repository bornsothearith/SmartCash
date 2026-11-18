"""Demo data contents and the 'fresh code after a push' guard."""
from datetime import date, timedelta

import pytest

from smartcash import auth, db, freshness
from smartcash import transactions as tx

PW = "secret123"
TODAY = date(2026, 11, 18)


@pytest.fixture
def conn_uid(tmp_path):
    c = db.connect(tmp_path / "demo.db")
    return c, auth.create_user(c, "demo_user", PW, PW)


# ---------------- demo data ----------------
def test_demo_income_is_varied_realistic_and_inside_8_weeks(conn_uid):
    c, uid = conn_uid
    added = tx.load_demo_income(c, uid, today=TODAY)
    rows = tx.filter_transactions(c, uid)
    assert added == len(rows) == tx.DEMO_INCOME >= 40
    assert all(r["tx_type"] == "income" and r["is_demo"] == 1 for r in rows)
    assert {r["category"] for r in rows} == {"Allowance", "Scholarship", "Part-time job", "Gift"}
    assert {r["currency"] for r in rows} == {"USD", "KHR"}
    days = [date.fromisoformat(r["tx_date"]) for r in rows]
    assert min(days) >= TODAY - timedelta(days=tx.DEMO_DAYS - 1) and max(days) <= TODAY
    assert sum(r["category"] == "Allowance" for r in rows) == 8      # one per week


def test_demo_expenses_spread_over_8_weeks(conn_uid):
    c, uid = conn_uid
    tx.load_demo_data(c, uid, n=tx.DEMO_EXPENSES, days=tx.DEMO_DAYS, today=TODAY)
    rows = tx.filter_transactions(c, uid)
    assert len(rows) == tx.DEMO_EXPENSES >= 30
    days = {date.fromisoformat(r["tx_date"]) for r in rows}
    assert min(days) >= TODAY - timedelta(days=tx.DEMO_DAYS - 1) and max(days) <= TODAY
    assert min(days) < TODAY - timedelta(days=28)      # really goes back further than 4 weeks


def test_demo_data_is_the_same_every_time(tmp_path):
    def load(name):
        c = db.connect(tmp_path / name)
        uid = auth.create_user(c, "u_" + name[:3], PW, PW)
        tx.load_demo_income(c, uid, today=TODAY)
        return [(r["tx_date"], r["amount"], r["category"]) for r in tx.filter_transactions(c, uid)]
    assert load("a.db") == load("b.db")


def test_remove_demo_keeps_real_rows(conn_uid):
    c, uid = conn_uid
    tx.add_transaction(c, uid, tx.Transaction(TODAY, "income", 5, "USD", "Gift", "Cash", "real"))
    tx.load_demo_income(c, uid, today=TODAY)
    tx.load_demo_data(c, uid, n=tx.DEMO_EXPENSES, days=tx.DEMO_DAYS, today=TODAY)
    tx.clear_demo_data(c, uid)
    assert [r["note"] for r in tx.filter_transactions(c, uid)] == ["real"]


# ---------------- fresh code after a push ----------------
def test_reload_only_when_files_changed(monkeypatch):
    monkeypatch.setattr(freshness, "_loaded_stamp", None)
    reloaded = []
    stamp = [100]
    run = lambda: freshness.reload_if_changed(lambda: stamp[0], lambda m: reloaded.append(m.__name__))
    assert run() is False and reloaded == []          # first run: just remember
    assert run() is False and reloaded == []          # nothing changed
    stamp[0] = 200                                    # a file changed (git push)
    assert run() is True
    assert "smartcash.transactions" in reloaded
    # modules are reloaded after the modules they import
    assert reloaded.index("smartcash.config") < reloaded.index("smartcash.rates") \
        < reloaded.index("smartcash.transactions") < reloaded.index("smartcash.diary_import")
    assert reloaded.index("smartcash.validation") < reloaded.index("smartcash.transactions")
    assert reloaded.index("smartcash.ui.theme") < reloaded.index("smartcash.ui.charts")
    reloaded.clear()
    assert run() is False and reloaded == []          # same stamp again: no extra reload


def test_reload_order_lists_every_module():
    """If someone adds a new smartcash module, they must add it to RELOAD_ORDER too."""
    root = freshness.PACKAGE_DIR
    found = set()
    for p in root.rglob("*.py"):
        parts = p.relative_to(root.parent).with_suffix("").parts
        name = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
        found.add(name)
    found -= {"smartcash", "smartcash.freshness"}
    assert found == set(freshness.RELOAD_ORDER), found ^ set(freshness.RELOAD_ORDER)
