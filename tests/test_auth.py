"""SCG-75 User accounts and data isolation."""
from datetime import date, datetime, timedelta

import pytest

from smartcash import auth, db
from smartcash import transactions as tx

PW = "secret123"


@pytest.fixture
def conn(tmp_path):
    return db.connect(tmp_path / "auth.db")


# ---- passwords are never stored ----
def test_password_is_hashed_not_stored(conn):
    auth.create_user(conn, "sokha", PW, PW)
    stored = conn.execute("SELECT password_hash FROM users").fetchone()[0]
    assert PW not in stored and stored.startswith("scrypt$")


def test_same_password_gives_different_hashes():
    assert auth.hash_password(PW) != auth.hash_password(PW)  # random salt


def test_verify_password():
    h = auth.hash_password(PW)
    assert auth.verify_password(PW, h)
    assert not auth.verify_password("secret124", h)
    assert not auth.verify_password(PW, "garbage")


# ---- sign up rules ----
@pytest.mark.parametrize("username, password, confirm", [
    ("ab", PW, PW),                       # username too short
    ("has space", PW, PW),                # bad characters
    ("dara", "short1", "short1"),         # password too short
    ("dara", "onlyletters", "onlyletters"),
    ("dara", "12345678", "12345678"),     # no letter
    ("dara99x", "dara99x", "dara99x"),    # same as username (too short anyway)
    ("dara", PW, "secret124"),            # confirm doesn't match
])
def test_bad_signups_are_rejected(conn, username, password, confirm):
    with pytest.raises(auth.SignupError):
        auth.create_user(conn, username, password, confirm)
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_username_must_be_unique_ignoring_case(conn):
    auth.create_user(conn, "Sokha", PW, PW)
    with pytest.raises(auth.SignupError, match="taken"):
        auth.create_user(conn, "sokha", PW, PW)


# ---- log in ----
def test_login_works_with_right_password(conn):
    uid = auth.create_user(conn, "sokha", PW, PW)
    assert auth.login(conn, "sokha", PW) == {"id": uid, "username": "sokha"}


def test_wrong_user_and_wrong_password_give_same_message(conn):
    auth.create_user(conn, "sokha", PW, PW)
    with pytest.raises(auth.LoginError) as a:
        auth.login(conn, "sokha", "wrongpass1")
    with pytest.raises(auth.LoginError) as b:
        auth.login(conn, "nobody", PW)
    assert str(a.value) == str(b.value) == auth.WRONG_LOGIN


def test_account_locks_after_5_wrong_passwords(conn):
    auth.create_user(conn, "sokha", PW, PW)
    now = datetime(2026, 11, 18, 9, 0)
    for _ in range(auth.MAX_FAILED_LOGINS):
        with pytest.raises(auth.LoginError):
            auth.login(conn, "sokha", "wrongpass1", now=now)
    with pytest.raises(auth.LoginError, match="Too many"):
        auth.login(conn, "sokha", PW, now=now + timedelta(minutes=1))  # right password, still locked
    later = now + timedelta(minutes=auth.LOCK_MINUTES + 1)
    assert auth.login(conn, "sokha", PW, now=later)["username"] == "sokha"


# ---- each user only sees their own data ----
def test_users_only_see_their_own_transactions(conn):
    a = auth.create_user(conn, "user_a", PW, PW)
    b = auth.create_user(conn, "user_b", PW, PW)
    tx.add_expense(conn, a, tx.Expense(date.today(), 5, "USD", "Transport", "Cash"))
    tx.load_demo_data(conn, b, n=3)
    assert len(tx.filter_transactions(conn, a)) == 1
    assert len(tx.filter_transactions(conn, b)) == 3
    tx.clear_demo_data(conn, b)
    assert len(tx.filter_transactions(conn, a)) == 1  # A's data untouched


def test_cannot_save_without_user(conn):
    with pytest.raises(ValueError):
        tx.add_expense(conn, None, tx.Expense(date.today(), 5, "USD", "Transport", "Cash"))


def test_old_sprint1_database_gets_user_id_column(tmp_path):
    import sqlite3
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.execute("CREATE TABLE transactions (id INTEGER PRIMARY KEY, tx_date TEXT, tx_type TEXT,"
                " amount REAL, currency TEXT, category TEXT, payment_method TEXT,"
                " note TEXT, is_demo INTEGER, created_at TEXT)")
    old.execute("INSERT INTO transactions VALUES (1,'2026-11-01','expense',3,'USD',"
                "'Other','Cash','',0,'')")
    old.commit()
    old.close()
    conn = db.connect(path)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(transactions)")}
    assert "user_id" in cols
    uid = auth.create_user(conn, "newuser", PW, PW)
    assert tx.filter_transactions(conn, uid) == []  # old rows belong to nobody
