"""SCG-68 Keep data private."""
import subprocess
from pathlib import Path

from smartcash import config

ROOT = Path(__file__).resolve().parents[1]


def is_ignored(path):
    r = subprocess.run(["git", "check-ignore", "-q", "--no-index", path], cwd=ROOT)
    return r.returncode == 0


def test_gitignore_blocks_private_files():
    for p in ["data/real/diary.csv", "data/synthetic/new.csv", "data/smartcash.db",
              ".env", ".streamlit/secrets.toml"]:
        assert is_ignored(p), f"{p} should be ignored by git"


def test_secret_comes_from_environment(monkeypatch):
    monkeypatch.setenv("SMARTCASH_TEST_SECRET", "from-env")
    assert config.get_secret("SMARTCASH_TEST_SECRET") == "from-env"


def test_missing_secret_returns_default(monkeypatch):
    monkeypatch.delenv("SMARTCASH_TEST_SECRET", raising=False)
    assert config.get_secret("SMARTCASH_TEST_SECRET", "none") == "none"
