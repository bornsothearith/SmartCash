"""SmartCash: Sprint 1 increment.

SCG-31 Add expense
SCG-33 View and filter transactions (styled with design-system/, see ui.py)
Run with:  streamlit run app.py
"""
from datetime import date, timedelta

import streamlit as st

import db
import ui

st.set_page_config(page_title="SmartCash", page_icon="💵", layout="wide")
ui.inject_css()

conn = db.connect()

st.title("SmartCash")
st.caption("Track what you spend in dollars and riel.")

add_tab, list_tab = st.tabs(["Add expense", "Transactions"])

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

# ---------------- SCG-33: View and filter ----------------
with list_tab:
    f1, f2, f3 = st.columns([2, 2, 1])
    default_start = date.today() - timedelta(days=30)
    period = f1.date_input("Dates", value=(default_start, date.today()))
    cats = f2.multiselect("Categories", db.EXPENSE_CATEGORIES,
                          placeholder="All categories")
    types = f3.multiselect("Type", ["expense", "income"], placeholder="All",
                           format_func=lambda t: "Income" if t == "income" else "Expense")

    start, end = (period if isinstance(period, tuple) and len(period) == 2
                  else (period[0] if isinstance(period, tuple) else period, None))
    rows = db.filter_transactions(conn, start, end, cats, types)

    if not rows:
        ui.html(ui.empty_card("No transactions match these filters",
                              "Add an expense, or widen the dates."))
    else:
        s = db.summarize(rows)
        c1, c2, c3 = st.columns(3)
        with c1:
            ui.html(ui.summary_card("Income", s["income"], "income",
                                    ui.plural(s["income_count"], "income entry", "income entries")))
        with c2:
            ui.html(ui.summary_card("Spending", s["spending"], "expense",
                                    ui.plural(s["expense_count"], "expense", "expenses")))
        with c3:
            ui.html(ui.summary_card("Net", s["net"], ui.net_direction(s["net"]),
                                    "Income minus spending", featured=True))
        st.caption(f"{ui.plural(s['count'], 'transaction', 'transactions')}. All totals in USD. Riel is converted at {db.KHR_PER_USD:,} KHR = $1 "
                   "for now (placeholder until the daily rate table, SCG-28).")
        ui.html(ui.transactions_table(rows))

with st.sidebar:
    st.subheader("Demo data")
    st.caption("Fake transactions for testing. Never mixed with real diary data.")
    if st.button("Add 30 demo expenses"):
        db.load_demo_data(conn)
        st.rerun()
    if st.button("Remove demo expenses"):
        db.clear_demo_data(conn)
        st.rerun()
