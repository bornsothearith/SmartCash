import sys, pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def never_use_the_real_database(monkeypatch):
    """Tests must NEVER touch the real (Neon) database from .streamlit/secrets.toml.

    Every test runs with "no DATABASE_URL", so the app uses a temporary SQLite file.
    tests/test_postgres.py opts in to its own throwaway PostgreSQL on purpose.
    """
    from smartcash import config
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(config, "database_url", lambda: None)
