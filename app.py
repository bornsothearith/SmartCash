"""SmartCash Sprint 2 Streamlit application.

Run with: streamlit run app.py
"""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import db
from smartcash.ui.theme import apply_theme

st.set_page_config(page_title="SmartCash", page_icon="💵", layout="wide")
apply_theme()
conn = db.connect()

st.title("SmartCash")
st.markdown('<div class="smart-subtitle">Track income and spending in dollars and riel.</div>', unsafe_allow_html=True)

add_tab, import_tab, list_tab, dashboard_tab = st.tabs([
    "Add transaction", "Import diary", "Transactions", "Dashboard"
])

with add_tab:
    tx_type = st.radio("Transaction type", ["expense", "income"], horizontal=True)
    currency = st.radio("Currency", db.CURRENCIES, horizontal=True)
    with st.form("add_transaction", clear_on_submit=True):
        c1, c2 = st.columns(2)
        tx_date = c1.date_input("Date", value=date.today(), max_value=date.today())
        amount = c2.number_input(
            "Amount", min_value=0.0,
            step=0.25 if currency == "USD" else 500.0,
            format="%.2f" if currency == "USD" else "%.0f",
        )
        c3, c4 = st.columns(2)
        category_options = db.EXPENSE_CATEGORIES if tx_type == "expense" else db.INCOME_CATEGORIES
        category = c3.selectbox("Category", category_options)
        payment = c4.selectbox("Paid with", db.PAYMENT_METHODS)
        note = st.text_input("Note (optional)", max_chars=200,
                             placeholder="e.g. lunch near campus")
        saved = st.form_submit_button("Save transaction", type="primary")

    if saved:
        transaction = db.Transaction(tx_date, tx_type, amount, currency,
                                      category, payment, note)
        problems = db.validate_transaction(transaction)
        if problems:
            for problem in problems:
                st.error(problem)
        else:
            db.add_transaction(conn, transaction)
            shown = f"${amount:,.2f}" if currency == "USD" else f"{amount:,.0f} KHR"
            st.success(f"Saved {tx_type}: {shown} - {category}.")

with import_tab:
    st.subheader("Import spending diary")
    st.caption("Required CSV columns: tx_date, tx_type, amount, currency, category, payment_method.")
    participant_id = st.text_input("Participant ID", placeholder="P001")
    uploaded = st.file_uploader("Choose a diary CSV", type="csv")
    if uploaded and st.button("Validate and import", type="primary"):
        try:
            result = db.import_csv(conn, uploaded, participant_id=participant_id.strip())
            st.success(f"Imported {result['imported']} row(s); skipped {result['duplicates']} duplicate(s).")
            if result["rejected"]:
                st.warning(f"Rejected {len(result['rejected'])} row(s).")
                st.dataframe(pd.DataFrame(result["rejected"]), hide_index=True, width="stretch")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
    st.download_button(
        "Download CSV template",
        "tx_date,tx_type,amount,currency,category,payment_method,note,is_demo\n"
        "2026-11-01,expense,3.50,USD,Food & drinks,Cash,lunch,1\n",
        file_name="smartcash_diary_template.csv",
        mime="text/csv",
    )

with list_tab:
    f1, f2, f3 = st.columns([2, 2, 1])
    default_start = date.today() - timedelta(days=30)
    period = f1.date_input("Dates", value=(default_start, date.today()))
    cats = f2.multiselect("Categories", db.EXPENSE_CATEGORIES + db.INCOME_CATEGORIES,
                          placeholder="All categories")
    types = f3.multiselect("Type", ["expense", "income"], placeholder="All")
    start, end = (period if isinstance(period, tuple) and len(period) == 2
                  else (period[0] if isinstance(period, tuple) else period, None))
    rows = db.filter_transactions(conn, start, end, cats, types)

    if not rows:
        st.info("No transactions match these filters. Add a transaction or widen the dates.")
    else:
        df = pd.DataFrame(rows)
        df["usd"] = [db.to_usd(a, c, date.fromisoformat(d), conn)
                      for a, c, d in zip(df.amount, df.currency, df.tx_date)]
        expenses = df.loc[df.tx_type == "expense", "usd"].sum()
        income = df.loc[df.tx_type == "income", "usd"].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Transactions", len(df))
        m2.metric("Spending (USD)", f"${expenses:,.2f}")
        m3.metric("Net (USD)", f"${income - expenses:,.2f}")
        st.caption("KHR uses the daily exchange-rate table; missing dates use the latest earlier rate.")
        show = df[["tx_date", "tx_type", "amount", "currency", "category",
                   "payment_method", "note"]].rename(columns={
            "tx_date": "Date", "tx_type": "Type", "amount": "Amount",
            "currency": "Currency", "category": "Category",
            "payment_method": "Paid with", "note": "Note"})
        st.dataframe(show, hide_index=True, width="stretch")

with dashboard_tab:
    st.subheader("Spending overview")
    rows = db.filter_transactions(conn)
    if not rows:
        st.info("Add or import transactions to see the dashboard.")
    else:
        df = pd.DataFrame(rows)
        df["usd"] = [db.to_usd(a, c, date.fromisoformat(d), conn)
                      for a, c, d in zip(df.amount, df.currency, df.tx_date)]
        expenses = df[df.tx_type == "expense"]
        income = df[df.tx_type == "income"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Income", f"${income.usd.sum():,.2f}")
        c2.metric("Spending", f"${expenses.usd.sum():,.2f}")
        c3.metric("Net cash flow", f"${income.usd.sum() - expenses.usd.sum():,.2f}")
        if not expenses.empty:
            by_category = expenses.groupby("category", as_index=False)["usd"].sum()
            st.bar_chart(by_category.set_index("category"))

with st.sidebar:
    st.subheader("Privacy notice")
    st.caption("Use synthetic data for demos. Do not enter names, account numbers, passwords, or real volunteer data in this local demo.")
    st.subheader("Demo data")
    st.caption("Fake transactions for testing. Never mixed with real diary data.")
    if st.button("Add 30 demo expenses"):
        db.load_demo_data(conn)
        st.rerun()
    if st.button("Remove demo expenses"):
        db.clear_demo_data(conn)
        st.rerun()
