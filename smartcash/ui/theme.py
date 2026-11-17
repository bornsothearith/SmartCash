"""Shared visual theme for the SmartCash Streamlit screens."""

import streamlit as st


def apply_theme() -> None:
    """Apply the white and light-gray SmartCash design system."""
    st.markdown(
        """
        <style>
        :root { --smart-navy:#172b4d; --smart-blue:#2563eb; --smart-teal:#0ea5a4; --smart-muted:#718096; --smart-border:#e5e7eb; --smart-panel:#f8fafc; }
        .stApp { background:#fff; color:var(--smart-navy); }
        [data-testid="stSidebar"] { background:var(--smart-panel); border-right:1px solid var(--smart-border); }
        [data-testid="stSidebar"] .stButton button { width:100%; }
        h1,h2,h3 { color:var(--smart-navy); letter-spacing:-.02em; }
        h1 { font-weight:750; }
        .smart-subtitle { color:var(--smart-muted); margin:-.55rem 0 1.25rem; }
        .smart-note { background:#eff6ff; border-radius:8px; color:#1d4ed8; padding:.8rem 1rem; }
        .smart-budget { border:1px solid var(--smart-border); border-radius:10px; padding:1rem 1.1rem; margin-bottom:.85rem; background:#fff; }
        .smart-budget-title { color:var(--smart-navy); font-size:1.05rem; font-weight:650; }
        .smart-budget-meta { color:var(--smart-muted); font-size:.9rem; }
        .smart-status { color:var(--smart-teal); font-weight:600; }
        div[data-testid="stMetric"] { background:var(--smart-panel); border:1px solid var(--smart-border); border-radius:10px; padding:.75rem 1rem; }
        .stButton > button,.stDownloadButton > button { border-radius:7px; border-color:#cbd5e1; }
        .stButton > button[kind="primary"] { background:var(--smart-blue); border-color:var(--smart-blue); }
        div[data-baseweb="input"] > div,div[data-baseweb="select"] > div,textarea { border-radius:7px; }
        div[data-testid="stDataFrame"] { border:1px solid var(--smart-border); border-radius:8px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
