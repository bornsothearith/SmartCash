"""Paths and secrets in one place (SCG-68).

Nothing secret is written in the code. Secrets come from an environment
variable or from Streamlit secrets (.streamlit/secrets.toml, never on GitHub).
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "smartcash.db"          # ignored by git (*.db)
RATES_CSV = DATA_DIR / "exchange_rates.csv"  # public NBC data, OK on git


def get_secret(name, default=None):
    """Read a secret (e.g. DB_PASSWORD) without hard-coding it.

    Order: environment variable first, then Streamlit secrets
    (.streamlit/secrets.toml locally, or the Secrets box on Streamlit Cloud).
    """
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:  # no streamlit, or no secrets.toml file
        return default
