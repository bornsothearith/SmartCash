"""Monthly category budgets page."""

from datetime import date

import pandas as pd
import streamlit as st

import db
from smartcash.ui.theme import apply_theme

st.set_page_config(page_title="SmartCash · Budgets", page_icon="💳", layout="wide")
apply_theme()
conn = db.connect()

if "budgets" not in st.session_state:
    st.session_state.budgets = {"Food & drinks": 120.0, "Transport": 45.0, "Shopping & personal care": 30.0, "Entertainment & social": 35.0}
if "show_budget_form" not in st.session_state:
    st.session_state.show_budget_form = False

header, action = st.columns([4, 1])
with header:
    st.title("Budgets")
    st.markdown('<div class="smart-subtitle">Set monthly spending limits and keep your daily spending on track.</div>', unsafe_allow_html=True)
with action:
    if st.button("+ Add budget", type="primary", use_container_width=True):
        st.session_state.show_budget_form = not st.session_state.show_budget_form

if st.session_state.show_budget_form:
    with st.form("add_budget"):
        st.subheader("Add budget")
        category = st.selectbox("Category", db.EXPENSE_CATEGORIES)
        limit = st.number_input("Monthly limit (USD)", min_value=1.0, value=50.0, step=5.0)
        if st.form_submit_button("Save budget", type="primary"):
            st.session_state.budgets[category] = limit
            st.session_state.show_budget_form = False
            st.success(f"Budget saved for {category}.")
            st.rerun()

rows = db.filter_transactions(conn, tx_types=["expense"])
spent = {category: 0.0 for category in st.session_state.budgets}
if rows:
    df = pd.DataFrame(rows)
    df["usd"] = [db.to_usd(amount, currency, date.fromisoformat(tx_date), conn) for amount, currency, tx_date in zip(df.amount, df.currency, df.tx_date)]
    spent.update(df.groupby("category")["usd"].sum().to_dict())

for category, limit in st.session_state.budgets.items():
    used = float(spent.get(category, 0.0))
    ratio = used / limit if limit else 0.0
    remaining = limit - used
    status = "Over budget" if ratio >= 1 else ("Slow down" if ratio >= .8 else "On track")
    st.markdown(f'<div class="smart-budget"><div class="smart-budget-title">{category}</div><div class="smart-budget-meta">${used:,.2f} used of ${limit:,.2f} · <span class="smart-status">{status}</span></div></div>', unsafe_allow_html=True)
    st.progress(min(ratio, 1.0))
    st.caption(f"${remaining:,.2f} left this month" if remaining >= 0 else f"${abs(remaining):,.2f} over the monthly limit")

st.markdown('<div class="smart-note">Tip: keep each category limit realistic, then review your Transactions page weekly.</div>', unsafe_allow_html=True)
