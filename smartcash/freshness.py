"""Keep the running app's code fresh after a git push.

Why: Streamlit re-reads app.py on every run, but it keeps the modules in
smartcash/ in memory. After a push to Streamlit Cloud, the app can run the NEW
app.py with the OLD smartcash code, e.g. "AttributeError: module has no
attribute 'load_demo_income'" (happened on 18 Nov 2026).

How: app.py calls reload_if_changed() before importing smartcash. If any .py
file in smartcash/ changed since it was loaded, every smartcash module is
reloaded, in an order where each module comes after the modules it imports.
Nothing happens when no file changed (the normal case).
"""
import importlib
import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent

# Each module is listed AFTER the smartcash modules it imports.
RELOAD_ORDER = [
    "smartcash.config",
    "smartcash.rates",
    "smartcash.validation.transaction_validation",
    "smartcash.validation.import_validation",
    "smartcash.validation.diary_schema",
    "smartcash.validation",
    "smartcash.transactions",
    "smartcash.database.postgres",
    "smartcash.database.connection",
    "smartcash.database",
    "smartcash.db",
    "smartcash.auth",
    "smartcash.diary_import",
    "smartcash.ui.theme",
    "smartcash.ui",
    "smartcash.theme",
    "smartcash.ui.charts",
    "smartcash.synthetic",
]

_loaded_stamp = None


def source_stamp():
    """Newest change time of any .py file in smartcash/."""
    return max(p.stat().st_mtime_ns for p in PACKAGE_DIR.rglob("*.py"))


def reload_if_changed(stamp_fn=source_stamp, reload_fn=importlib.reload):
    """Reload all smartcash modules if their files changed. Returns True if it reloaded."""
    global _loaded_stamp
    stamp = stamp_fn()
    if _loaded_stamp is None:          # first run in this process: just remember
        _loaded_stamp = stamp
        return False
    if stamp == _loaded_stamp:
        return False
    for name in RELOAD_ORDER:
        if name in sys.modules:
            reload_fn(sys.modules[name])
    _loaded_stamp = stamp
    return True
