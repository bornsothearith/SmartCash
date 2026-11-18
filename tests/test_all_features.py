"""Click-through of EVERY screen and button in the app (no browser needed).

Each test logs in as a fake user on a temporary database and uses the app
the way a person would. Fake data only.
"""
from datetime import date, timedelta

import pytest
from streamlit.testing.v1 import AppTest

from smartcash import auth, config, db
from smartcash import transactions as tx

PW = "secret123"
PAGES = ["Overview", "Transactions", "Budgets", "Forecast", "Study Insights",
         "Add transaction", "Import diary"]


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "app.db")
    monkeypatch.setattr(config, "database_url", lambda: None)   # never touch a real database
    return AppTest.from_file("../app.py", default_timeout=30)


@pytest.fixture
def user(app):
    c = db.connect()
    uid = auth.create_user(c, "tester1", PW, PW)
    app.session_state["user"] = {"id": uid, "username": "tester1"}
    return c, uid


def expense(amount=3.5, currency="USD", category="Transport", days_ago=0, note=""):
    return tx.Transaction(date.today() - timedelta(days=days_ago), "expense", amount,
                          currency, category, "Cash", note)


def button(app, label):
    return next(b for b in app.button if b.label == label)


def go(app, page):
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception, app.exception


def text(app):
    return " ".join(m.value for m in app.markdown)


# ---------------- every page opens, with and without data ----------------
@pytest.mark.parametrize("page", PAGES)
def test_every_page_opens_with_no_data(app, user, page):
    app.run()
    go(app, page)


@pytest.mark.parametrize("page", PAGES)
def test_every_page_opens_with_demo_data(app, user, page):
    c, uid = user
    tx.load_demo_data(c, uid, n=50)
    tx.add_transaction(c, uid, tx.Transaction(date.today(), "income", 60, "USD",
                                              "Allowance", "Cash"))
    app.run()
    go(app, page)


# ---------------- EDIT (the bug from the screenshot) ----------------
def test_edit_opens_without_crash_and_saves(app, user):
    c, uid = user
    row_id = tx.add_transaction(c, uid, expense(5000, "KHR", note="old"))
    app.run()
    button(app, "Edit").click().run()
    assert not app.exception, app.exception
    assert app.title[0].value == "Edit transaction"
    assert app.number_input[0].value == 5000              # pre-filled
    assert app.text_input[0].value == "old"
    app.number_input[0].set_value(8000)
    app.text_input[0].set_value("new")
    button(app, "Save changes").click().run()
    assert not app.exception, app.exception
    assert app.title[0].value == "Transactions"           # back on the list
    assert any("Updated" in s.value for s in app.success)
    row = tx.filter_transactions(c, uid)[0]
    assert (row["id"], row["amount"], row["note"]) == (row_id, 8000, "new")


def test_edit_can_switch_expense_to_income(app, user):
    c, uid = user
    tx.add_transaction(c, uid, expense())
    app.run()
    button(app, "Edit").click().run()
    next(r for r in app.radio if r.label == "Transaction type").set_value("income").run()
    assert app.selectbox[0].label == "Income source"
    app.selectbox[0].set_value("Scholarship")
    button(app, "Save changes").click().run()
    assert not app.exception, app.exception
    row = tx.filter_transactions(c, uid)[0]
    assert (row["tx_type"], row["category"]) == ("income", "Scholarship")


def test_edit_with_bad_amount_shows_error_and_keeps_old_value(app, user):
    c, uid = user
    tx.add_transaction(c, uid, expense(4))
    app.run()
    button(app, "Edit").click().run()
    app.number_input[0].set_value(0)
    button(app, "Save changes").click().run()
    assert any("more than 0" in e.value for e in app.error)
    assert app.title[0].value == "Edit transaction"
    assert tx.filter_transactions(c, uid)[0]["amount"] == 4


@pytest.mark.parametrize("way_out", ["back", "menu"])
def test_can_leave_edit_page(app, user, way_out):
    c, uid = user
    tx.add_transaction(c, uid, expense())
    app.run()
    button(app, "Edit").click().run()
    if way_out == "back":
        button(app, "← Back to transactions").click().run()
        assert app.title[0].value == "Transactions"
    else:
        go(app, "Overview")
        assert app.title[0].value == "Overview"
    assert not app.exception


def test_edit_a_second_row_shows_that_rows_values(app, user):
    c, uid = user
    tx.add_transaction(c, uid, expense(3, days_ago=1))
    tx.add_transaction(c, uid, expense(9, days_ago=0))
    app.run()
    button(app, "Edit").click().run()                      # newest first -> 9
    assert app.number_input[0].value == 9
    button(app, "← Back to transactions").click().run()
    [b for b in app.button if b.label == "Edit"][1].click().run()
    assert app.number_input[0].value == 3


# ---------------- DELETE ----------------
def test_delete_asks_under_the_row_then_deletes(app, user):
    c, uid = user
    tx.add_transaction(c, uid, expense(42))
    tx.add_transaction(c, uid, expense(7, days_ago=1))
    app.run()
    button(app, "Delete").click().run()
    assert any("42.00 USD" in w.value and "can't be undone" in w.value for w in app.warning)
    button(app, "Cancel").click().run()
    assert len(tx.filter_transactions(c, uid)) == 2 and not app.warning
    button(app, "Delete").click().run()
    button(app, "Yes, delete").click().run()
    assert not app.exception
    assert [r["amount"] for r in tx.filter_transactions(c, uid)] == [7]
    assert any("Deleted" in s.value for s in app.success)


def test_delete_question_closes_when_leaving_page(app, user):
    c, uid = user
    tx.add_transaction(c, uid, expense())
    app.run()
    button(app, "Delete").click().run()
    go(app, "Overview")
    go(app, "Transactions")
    assert not app.warning and len(tx.filter_transactions(c, uid)) == 1


# ---------------- ADD ----------------
@pytest.mark.parametrize("kind, category", [("expense", "Transport"), ("income", "Allowance")])
def test_add_expense_and_income(app, user, kind, category):
    c, uid = user
    app.run()
    button(app, "+ Add transaction").click().run()
    assert app.title[0].value == "Add transaction"
    next(r for r in app.radio if r.label == "Transaction type").set_value(kind).run()
    app.number_input[0].set_value(12)
    app.selectbox[0].set_value(category)
    button(app, "Save transaction").click().run()
    assert not app.exception
    assert any("Saved" in s.value for s in app.success)
    row = tx.filter_transactions(c, uid)[0]
    assert (row["tx_type"], row["category"], row["amount"]) == (kind, category, 12)


def test_add_khr_shows_rate_and_usd(app, user):
    app.run()
    go(app, "Add transaction")
    next(r for r in app.radio if r.label == "Currency").set_value("KHR").run()
    assert "KHR = $1" in text(app)
    app.number_input[0].set_value(4000)
    button(app, "Save transaction").click().run()
    assert any("4,000 KHR" in s.value and "≈" in s.value for s in app.success)


# ---------------- LIST, FILTERS, EXPORT ----------------
def test_type_filter_and_totals(app, user):
    c, uid = user
    tx.add_transaction(c, uid, expense(10))
    tx.add_transaction(c, uid, tx.Transaction(date.today(), "income", 50, "USD", "Gift", "Cash"))
    app.run()
    html = text(app)
    assert "$50.00" in html and "$10.00" in html and "$40.00" in html   # income, spending, net
    app.multiselect[1].set_value(["income"]).run()
    assert any("1 transactions" in c_.value for c_ in app.caption)


def test_export_button_is_there(app, user):
    c, uid = user
    tx.add_transaction(c, uid, expense())
    app.run()
    assert "Export CSV" in str(app)  # download button rendered


# ---------------- DEMO DATA ----------------
def test_demo_data_add_and_remove(app, user):
    c, uid = user
    app.run()
    tx.add_transaction(c, uid, expense(note="my own"))          # real row must survive
    app.run()
    button(app, f"Add demo data ({tx.DEMO_EXPENSES} expenses + {tx.DEMO_INCOME} income)").click().run()
    assert not app.exception, app.exception
    rows = tx.filter_transactions(c, uid)
    assert sum(r["tx_type"] == "expense" and r["is_demo"] for r in rows) == tx.DEMO_EXPENSES >= 30
    income = [r for r in rows if r["tx_type"] == "income"]
    assert len(income) == tx.DEMO_INCOME >= 40 and all(r["is_demo"] for r in income)
    assert {r["category"] for r in income} <= set(tx.INCOME_CATEGORIES)
    assert "$" in text(app) and not app.exception                # totals show income
    button(app, "Remove demo data").click().run()
    assert [r["note"] for r in tx.filter_transactions(c, uid)] == ["my own"]


# ---------------- BUDGETS ----------------
def test_budgets_use_real_categories_and_show_dollars_safely(app, user):
    c, uid = user
    tx.add_transaction(c, uid, expense(20, category="Transport",
                                       days_ago=0))
    app.run()
    go(app, "Budgets")
    html = text(app)
    assert "Transport" in html and "\\$20.00 of \\$45.00" in html   # matches real spending
    assert "On track" in html or "Watch" in html or "Over budget" in html


def test_budget_can_be_saved(app, user):
    app.run()
    go(app, "Budgets")
    app.selectbox[0].set_value("Groceries")
    app.number_input[0].set_value(80)
    button(app, "Save budget").click().run()
    assert any("Budget saved" in s.value for s in app.success)
    assert "Groceries" in text(app)


# ---------------- LOG OUT ----------------
def test_log_out_clears_everything(app, user):
    app.run()
    button(app, "Log out").click().run()
    assert app.title[0].value == "Welcome to SmartCash"
    assert "user" not in app.session_state


@pytest.mark.parametrize("page", PAGES)
def test_every_page_opens_after_demo_button(app, user, page):
    """The exact path that broke on the live app: click the demo button, then visit every page."""
    app.run()
    button(app, f"Add demo data ({tx.DEMO_EXPENSES} expenses + {tx.DEMO_INCOME} income)").click().run()
    assert not app.exception, app.exception
    go(app, page)
