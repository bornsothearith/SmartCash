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
    st.caption("Illustrative dashboard layout based on the DataViz proposal.")

    filter_date, filter_category = st.columns([2, 2])
    dashboard_period = filter_date.date_input(
        "Period", value=(date.today() - timedelta(days=180), date.today())
    )
    dashboard_categories = filter_category.multiselect(
        "Category", db.EXPENSE_CATEGORIES, placeholder="All categories"
    )
    if isinstance(dashboard_period, tuple) and len(dashboard_period) == 2:
        dashboard_start, dashboard_end = dashboard_period
    else:
        dashboard_start, dashboard_end = date.today() - timedelta(days=180), date.today()

    rows = db.filter_transactions(conn, dashboard_start, dashboard_end, dashboard_categories)
    if not rows:
        st.info("Add or import transactions to see the dashboard charts.")
    else:
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["tx_date"])
        df["usd"] = [db.to_usd(amount, currency, tx_date.date(), conn)
                      for amount, currency, tx_date in zip(df.amount, df.currency, df.date)]
        expenses = df[df.tx_type == "expense"].copy()
        income = df[df.tx_type == "income"].copy()
        income_total = income.usd.sum()
        spending_total = expenses.usd.sum()
        net_total = income_total - spending_total
        savings_rate = (net_total / income_total * 100) if income_total else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Income", f"${income_total:,.2f}")
        c2.metric("Spending", f"${spending_total:,.2f}")
        c3.metric("Net cash flow", f"${net_total:,.2f}")
        c4.metric("Savings rate", f"{savings_rate:.1f}%")

        if expenses.empty:
            st.info("No expense records match these filters yet.")
        else:
            weekly = expenses.set_index("date")["usd"].resample("W-SUN").sum().rename("Weekly spending")
            trend = weekly.to_frame()
            trend["4-week average"] = weekly.rolling(4, min_periods=1).mean()
            left_chart, right_chart = st.columns([3, 2])
            with left_chart:
                st.markdown("**Weekly spending (USD)**")
                st.line_chart(trend, y_label="USD", x_label="Week")
            with right_chart:
                st.markdown("**Top categories this period**")
                by_category = (expenses.groupby("category", as_index=False)["usd"].sum()
                               .sort_values("usd", ascending=True)
                               .set_index("category"))
                st.bar_chart(by_category, y="usd", horizontal=True, x_label="USD")
            st.caption("Solid line = weekly spending. Dashed-style comparison = four-week average. All amounts are USD equivalents.")

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
