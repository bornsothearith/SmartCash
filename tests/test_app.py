"""Runs the real Streamlit app (no browser) to check the screens work."""
from datetime import date

import pytest
from streamlit.testing.v1 import AppTest

from smartcash import auth, config, db
from smartcash import transactions as tx

PW = "secret123"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "app.db")
    return AppTest.from_file("../app.py", default_timeout=30)


def logged_in(app, username="tester1"):
    """Make an account and open the app as that user."""
    uid = auth.create_user(db.connect(), username, PW, PW)
    app.session_state["user"] = {"id": uid, "username": username}
    app.run()
    return uid


def click(app, label):
    next(b for b in app.button if b.label == label).click().run()


# ---- SCG-75 login screen ----
def test_not_logged_in_shows_login_page(app):
    app.run()
    assert not app.exception
    assert app.title[0].value == "Welcome to SmartCash"
    assert [t.label for t in app.tabs] == ["Log in", "Sign up"]


def test_sign_up_then_see_transactions(app):
    app.run()
    app.text_input[2].input("newuser")      # Sign up: username
    app.text_input[3].input(PW)             # password
    app.text_input[4].input(PW)             # confirm
    click(app, "Create account")
    assert not app.exception
    assert app.title[0].value == "Transactions"


def test_wrong_password_shows_error(app):
    auth.create_user(db.connect(), "tester1", PW, PW)
    app.run()
    app.text_input[0].input("tester1")
    app.text_input[1].input("wrongpass1")
    click(app, "Log in")
    assert any(auth.WRONG_LOGIN in e.value for e in app.error)
    assert "user" not in app.session_state


def test_log_in_and_log_out(app):
    auth.create_user(db.connect(), "tester1", PW, PW)
    app.run()
    app.text_input[0].input("tester1")
    app.text_input[1].input(PW)
    click(app, "Log in")
    assert app.title[0].value == "Transactions"
    click(app, "Log out")
    assert app.title[0].value == "Welcome to SmartCash"


# ---- main screens ----
def test_transactions_page_empty(app):
    logged_in(app)
    assert not app.exception
    assert any("No transactions" in i.value for i in app.info)


def test_transactions_page_shows_usd_and_rate(app):
    conn = db.connect()
    uid = auth.create_user(conn, "tester1", PW, PW)
    tx.add_expense(conn, uid, tx.Expense(date.today(), 8000, "KHR", "Transport", "Cash"))
    app.session_state["user"] = {"id": uid, "username": "tester1"}
    app.run()
    assert not app.exception
    html = " ".join(m.value for m in app.markdown)
    assert "8,000 KHR" in html and "KHR = $1" in html


def test_other_users_data_is_hidden(app):
    conn = db.connect()
    other = auth.create_user(conn, "someone", PW, PW)
    tx.add_expense(conn, other, tx.Expense(date.today(), 8000, "KHR", "Transport", "Cash"))
    logged_in(app, "tester1")
    assert any("No transactions" in i.value for i in app.info)


def test_add_expense_saves_it(app):
    uid = logged_in(app)
    app.sidebar.radio[0].set_value("Add transaction").run()
    assert app.title[0].value == "Add transaction"
    app.number_input[0].set_value(3.5)
    click(app, "Save transaction")
    assert not app.exception
    assert any("Saved" in s.value for s in app.success)
    assert len(tx.filter_transactions(db.connect(), uid)) == 1


def test_bad_expense_shows_error(app):
    uid = logged_in(app)
    app.sidebar.radio[0].set_value("Add transaction").run()
    click(app, "Save transaction")  # amount still 0
    assert any("more than 0" in e.value for e in app.error)
    assert tx.filter_transactions(db.connect(), uid) == []
