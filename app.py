"""SmartCash

SCG-31 Add expense
SCG-30 Add income
SCG-33 View and filter transactions (Income, Spending and Net shown separately)
Run with:  streamlit run app.py
"""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import db

st.set_page_config(page_title="SmartCash", page_icon="💵", layout="wide")

conn = db.connect()

st.title("SmartCash")
st.caption("Track what you spend in dollars and riel.")

add_tab, income_tab, list_tab = st.tabs(["Add expense", "Add income", "Transactions"])

# ---------------- SCG-31: Add expense ----------------
with add_tab:
    # Outside the form so the amount box switches to whole riel straight away.
    currency = st.radio("Currency", db.CURRENCIES, horizontal=True)
    with st.form("add_expense", clear_on_submit=True):
        c1, c3 = st.columns(2)
        tx_date = c1.date_input("Date", value=date.today(), max_value=date.today())
        amount = c3.number_input(
            "Amount", min_value=0.0,
            step=0.25 if currency == "USD" else 500.0,
            format="%.2f" if currency == "USD" else "%.0f",
        )
        c4, c5 = st.columns(2)
        category = c4.selectbox("Category", db.EXPENSE_CATEGORIES)
        payment = c5.selectbox("Paid with", db.PAYMENT_METHODS)
        note = st.text_input("Note (optional)", max_chars=200,
                             placeholder="e.g. lunch near campus")
        saved = st.form_submit_button("Save expense", type="primary")

    if saved:
        expense = db.Expense(tx_date, amount, currency, category, payment, note)
        problems = db.validate_expense(expense)
        if problems:
            for p in problems:
                st.error(p)
        else:
            db.add_expense(conn, expense)
            shown = f"${amount:,.2f}" if currency == "USD" else f"{amount:,.0f} KHR"
            st.success(f"Saved: {shown} on {category}.")

# ---------------- SCG-30: Add income ----------------
with income_tab:
    in_currency = st.radio("Currency", db.CURRENCIES, horizontal=True, key="income_currency")
    with st.form("add_income", clear_on_submit=True):
        c1, c2 = st.columns(2)
        in_date = c1.date_input("Date", value=date.today(), max_value=date.today(),
                                key="income_date")
        in_amount = c2.number_input(
            "Amount", min_value=0.0, key="income_amount",
            step=1.0 if in_currency == "USD" else 1000.0,
            format="%.2f" if in_currency == "USD" else "%.0f",
        )
        c3, c4 = st.columns(2)
        in_type = c3.selectbox("Income type", db.INCOME_TYPES)
        received = c4.selectbox("Received as (optional)", db.PAYMENT_METHODS,
                                index=None, placeholder="Not given")
        in_note = st.text_input("Note (optional)", max_chars=200, key="income_note",
                                placeholder="e.g. monthly allowance from parents")
        in_saved = st.form_submit_button("Save income", type="primary")

    if in_saved:
        income = db.Income(in_date, in_amount, in_currency, in_type, received or "", in_note)
        problems = db.validate_income(income)
        if problems:
            for p in problems:
                st.error(p)
        else:
            db.add_income(conn, income)
            shown = f"${in_amount:,.2f}" if in_currency == "USD" else f"{in_amount:,.0f} KHR"
            st.success(f"Saved: {shown} income ({in_type}).")

# ---------------- SCG-33: View and filter ----------------
with list_tab:
    f1, f2, f3 = st.columns([2, 2, 1])
    default_start = date.today() - timedelta(days=30)
    period = f1.date_input("Dates", value=(default_start, date.today()))
    all_cats = db.EXPENSE_CATEGORIES + [t for t in db.INCOME_TYPES if t not in db.EXPENSE_CATEGORIES]
    cats = f2.multiselect("Categories", all_cats, placeholder="All categories")
    types = f3.multiselect("Type", ["income", "expense"], placeholder="All",
                           format_func=lambda t: "Income" if t == "income" else "Expense")

    start, end = (period if isinstance(period, tuple) and len(period) == 2
                  else (period[0] if isinstance(period, tuple) else period, None))
    rows = db.filter_transactions(conn, start, end, cats, types)

    if not rows:
        st.info("No transactions match these filters. Add an expense, or widen the dates.")
    else:
        s = db.summarize(rows)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Income (USD)", f"${s['income']:,.2f}")
        m2.metric("Spending (USD)", f"${s['spending']:,.2f}")
        net = s["net"]
        m3.metric("Net (USD)", f"{'−' if net < 0 else ''}${abs(net):,.2f}")
        m4.metric("Transactions", s["count"])
        st.caption(f"Riel is converted at {db.KHR_PER_USD:,} KHR = $1 for now "
                   "(placeholder until the daily rate table, SCG-28).")
        df = pd.DataFrame(rows)
        df["tx_type"] = df["tx_type"].map({"income": "Income", "expense": "Expense"})
        show = df[["tx_date", "tx_type", "amount", "currency", "category",
                   "payment_method", "note"]].rename(columns={
            "tx_date": "Date", "tx_type": "Type", "amount": "Amount",
            "currency": "Currency", "category": "Category",
            "payment_method": "Paid / received", "note": "Note"})
        st.dataframe(show, hide_index=True, width="stretch")

with st.sidebar:
    st.subheader("Demo data")
    st.caption("Fake transactions for testing. Never mixed with real diary data.")
    if st.button("Add demo data (30 expenses, 4 income)"):
        db.load_demo_data(conn)
        db.load_demo_income(conn)
        st.rerun()
    if st.button("Remove demo data"):
        db.clear_demo_data(conn)
        st.rerun()
