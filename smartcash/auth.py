"""SCG-75 User accounts: sign up and log in.

How passwords are kept safe
- We never save the password. We save a scrypt hash with a random salt.
  (scrypt is built into Python: hashlib.scrypt. It is slow on purpose,
  so guessing many passwords takes a long time.)
- Checking a password uses hmac.compare_digest (same time for every guess).
- Wrong username and wrong password give the SAME message, so nobody can
  find out which usernames exist.
- After 5 wrong passwords the account is locked for 5 minutes.
- Usernames only. No real names, emails or phone numbers (SCG-68).
"""
import base64
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta

USERNAME_RULE = re.compile(r"^[A-Za-z0-9_.]{3,30}$")
MIN_PASSWORD, MAX_PASSWORD = 8, 128
MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 5
_N, _R, _P = 2 ** 14, 8, 1   # scrypt cost settings
WRONG_LOGIN = "Wrong username or password."


class LoginError(Exception):
    pass


class SignupError(ValueError):
    """Sign-up problems. `problems` is a list of short messages."""
    def __init__(self, problems):
        super().__init__(" ".join(problems))
        self.problems = problems


def _b64(raw):
    return base64.b64encode(raw).decode("ascii")


def hash_password(password):
    """Return 'scrypt$n$r$p$salt$hash'. A new random salt every time."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(digest)}"


def verify_password(password, stored):
    try:
        algo, n, r, p, salt, digest = stored.split("$")
        if algo != "scrypt":
            return False
        expected = base64.b64decode(digest)
        got = hashlib.scrypt(password.encode("utf-8"), salt=base64.b64decode(salt),
                             n=int(n), r=int(r), p=int(p), dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(got, expected)


# Used when the username does not exist, so the answer takes the same time.
_DUMMY_HASH = hash_password(secrets.token_hex(8))


def validate_signup(username, password, confirm):
    """Return a list of problems. Empty list means OK."""
    errors = []
    if not USERNAME_RULE.match(username or ""):
        errors.append("Username: 3 to 30 letters, numbers, _ or . (no spaces).")
    if len(password or "") < MIN_PASSWORD:
        errors.append(f"Password must be at least {MIN_PASSWORD} characters.")
    elif len(password) > MAX_PASSWORD:
        errors.append(f"Password must be {MAX_PASSWORD} characters or fewer.")
    elif not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
        errors.append("Password needs at least one letter and one number.")
    if password and username and password.lower() == username.lower():
        errors.append("Password can't be the same as the username.")
    if password != confirm:
        errors.append("The two passwords are not the same.")
    return errors


def create_user(conn, username, password, confirm):
    """Make a new account. Returns the user id. Raises SignupError with reasons."""
    username = (username or "").strip()
    errors = validate_signup(username, password, confirm)
    if errors:
        raise SignupError(errors)
    taken = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
    if taken:
        raise SignupError(["That username is taken. Try another one."])
    cur = conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                       (username, hash_password(password)))
    conn.commit()
    return cur.lastrowid


def login(conn, username, password, now=None):
    """Return {'id', 'username'} if the password is right. Else raise LoginError."""
    now = now or datetime.now()
    username = (username or "").strip()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user is None:
        verify_password(password or "", _DUMMY_HASH)   # same time as a real check
        raise LoginError(WRONG_LOGIN)

    if user["locked_until"] and datetime.fromisoformat(user["locked_until"]) > now:
        raise LoginError(f"Too many wrong tries. Wait {LOCK_MINUTES} minutes and try again.")

    if not verify_password(password or "", user["password_hash"]):
        failed = user["failed_logins"] + 1
        locked = None
        if failed >= MAX_FAILED_LOGINS:
            failed, locked = 0, (now + timedelta(minutes=LOCK_MINUTES)).isoformat()
        conn.execute("UPDATE users SET failed_logins = ?, locked_until = ? WHERE id = ?",
                     (failed, locked, user["id"]))
        conn.commit()
        raise LoginError(WRONG_LOGIN)

    conn.execute("UPDATE users SET failed_logins = 0, locked_until = NULL WHERE id = ?",
                 (user["id"],))
    conn.commit()
    return {"id": user["id"], "username": user["username"]}
