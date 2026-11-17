"""SmartCash app. Run with:  streamlit run app.py

SCG-75 Log in / sign up        -> each user only sees their own data
SCG-31 Add expense, SCG-33 View and filter
SCG-28 Daily USD/KHR rate
Look: docs/design/smartcash-ui-design.pdf
"""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from smartcash import auth, db, rates, theme
from smartcash import transactions as tx

st.set_page_config(page_title="SmartCash", page_icon="💵", layout="wide")
st.markdown(theme.CSS, unsafe_allow_html=True)

conn = db.connect()

PAGES = ["Transactions", "Add transaction"]
st.session_state.setdefault("page", PAGES[0])


def go_to_add():
    st.session_state.page = "Add transaction"


def log_out():
    # Forget everything about this session (user, filters, form values).
    for key in list(st.session_state.keys()):
        del st.session_state[key]


# ---------------- SCG-75: Log in / Sign up ----------------
def auth_page():
    with st.sidebar:
        st.markdown(theme.BRAND, unsafe_allow_html=True)
        st.markdown(theme.PRIVACY, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.title("Welcome to SmartCash")
        st.caption("Log in to see your own spending. Nobody else can see it.")
        login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

        with login_tab:
            with st.form("login", clear_on_submit=True):
                username = st.text_input("Username", autocomplete="username")
                password = st.text_input("Password", type="password",
                                         autocomplete="current-password")
                sent = st.form_submit_button("Log in", type="primary",
                                             use_container_width=True)
            if sent:
                try:
                    st.session_state.user = auth.login(conn, username, password)
                    st.rerun()
                except auth.LoginError as e:
                    st.error(str(e))

        with signup_tab:
            st.markdown(
                "<div class='sc-note'><b>Privacy</b>Pick a nickname, not your real "
                "name. We never ask for your email, phone or bank details.</div>",
                unsafe_allow_html=True)
            with st.form("signup", clear_on_submit=True):
                new_user = st.text_input("Username", autocomplete="username",
                                         help="3–30 letters, numbers, _ or .")
                new_pw = st.text_input("Password", type="password",
                                       autocomplete="new-password",
                                       help="At least 8 characters, with a letter and a number.")
                confirm = st.text_input("Type the password again", type="password",
                                        autocomplete="new-password")
                made = st.form_submit_button("Create account", type="primary",
                                             use_container_width=True)
            if made:
                try:
                    uid = auth.create_user(conn, new_user, new_pw, confirm)
                    st.session_state.user = {"id": uid, "username": new_user.strip()}
                    st.rerun()
                except auth.SignupError as e:
                    for problem in e.problems:
                        st.error(problem)


# ---------------- SCG-33: Transactions list ----------------
def transactions_page(user_id):
    h1, h2 = st.columns([4, 1], vertical_alignment="bottom")
    h1.title("Transactions")
    h1.caption("Review, filter, and add expenses.")
    h2.button("+ Add transaction", type="primary", on_click=go_to_add,
              use_container_width=True)

    with st.container(border=True):
        f1, f2, f3 = st.columns([2, 2, 1])
        default_start = date.today() - timedelta(days=30)
        period = f1.date_input("Dates", value=(default_start, date.today()))
        cats = f2.multiselect("Category", tx.EXPENSE_CATEGORIES,
                              placeholder="All categories")
        types = f3.multiselect("Type", ["expense", "income"], placeholder="All")

    start, end = (period if isinstance(period, tuple) and len(period) == 2
                  else (period[0] if isinstance(period, tuple) else period, None))
    rows = tx.filter_transactions(conn, user_id, start, end, cats, types)

    if not rows:
        st.info("No transactions match these filters. Add an expense, or widen the dates.")
        return

    for r in rows:
        r["rate"] = (rates.rate_used(date.fromisoformat(r["tx_date"]))
                     if r["currency"] == "KHR" else None)
        r["usd"] = tx.to_usd(r["amount"], r["currency"], r["tx_date"])
    df = pd.DataFrame(rows)
    spend = df.loc[df.tx_type == "expense", "usd"].sum()
    income = df.loc[df.tx_type == "income", "usd"].sum()
    khr_share = (df.currency == "KHR").mean()
    today_rate = rates.rate_used(date.today())

    st.markdown(theme.cards([
        ("Transactions", f"{len(df)}", "in this view", theme.BLUE),
        ("Total spending", f"${spend:,.2f}", "USD equivalent", theme.AMBER),
        ("Paid in riel", f"{khr_share:.0%}", "of transactions", theme.TEAL),
        ("Rate used today", f"{today_rate.khr_per_usd:,.0f}",
         "KHR = $1 · NBC" + (" (earlier day)" if today_rate.filled else ""), theme.GREEN),
    ]), unsafe_allow_html=True)
    if income:
        st.caption(f"Income in this view: \\${income:,.2f}")

    st.markdown(theme.tx_table(rows), unsafe_allow_html=True)
    st.caption("USD uses the National Bank of Cambodia official rate of each "
               "transaction's day. On days with no official rate (weekends, "
               "holidays) the last earlier rate is used and its date is shown.")

    export = df[["tx_date", "tx_type", "amount", "currency", "usd", "category",
                 "payment_method", "note"]].round({"usd": 2})
    st.download_button("Export CSV", export.to_csv(index=False).encode("utf-8"),
                       "smartcash_transactions.csv", "text/csv")


# ---------------- SCG-31: Add transaction ----------------
def add_page(user_id):
    st.title("Add transaction")
    st.caption("Record it now. Understand it later.")

    with st.container(border=True):
        st.markdown("**Type:** Expense")
        st.caption("Income comes with SCG-30.")
        # Outside the form so the amount box and the rate update straight away.
        c1, c2 = st.columns(2)
        currency = c1.radio("Currency", tx.CURRENCIES, horizontal=True)
        tx_date = c2.date_input("Date", value=date.today(), max_value=date.today())
        rate = rates.rate_used(tx_date)
        if currency == "KHR":
            st.markdown(f"<div class='sc-note'><b>Rate used</b>{theme.rate_text(rate)}"
                        " · National Bank of Cambodia</div>", unsafe_allow_html=True)

        with st.form("add_expense", clear_on_submit=True, border=False):
            c3, c4 = st.columns(2)
            amount = c3.number_input(
                f"Amount ({currency})", min_value=0.0,
                step=0.25 if currency == "USD" else 500.0,
                format="%.2f" if currency == "USD" else "%.0f",
            )
            category = c4.selectbox("Category", tx.EXPENSE_CATEGORIES)
            c5, c6 = st.columns(2)
            payment = c5.selectbox("Paid with", tx.PAYMENT_METHODS)
            note = c6.text_input("Note (optional)", max_chars=200,
                                 placeholder="e.g. lunch near campus")
            saved = st.form_submit_button("Save transaction", type="primary")

    if saved:
        expense = tx.Expense(tx_date, amount, currency, category, payment, note)
        problems = tx.validate_expense(expense)
        if problems:
            for p in problems:
                st.error(p)
        else:
            tx.add_expense(conn, user_id, expense)
            shown = theme.money(amount, currency)
            if currency == "KHR":
                shown += f" (≈ ${tx.to_usd(amount, currency, tx_date):,.2f} at {theme.rate_text(rate)})"
            # "\$" so Streamlit doesn't read "$...$" as a maths formula
            st.success(f"Saved: {shown} on {category}.".replace("$", "\\$"))


# ---------------- Main app (logged in) ----------------
def main_app(user):
    with st.sidebar:
        st.markdown(theme.BRAND, unsafe_allow_html=True)
        st.caption("WORKSPACE")
        st.radio("Menu", PAGES, key="page", label_visibility="collapsed")
        st.caption("Overview, Budgets and Forecast come in later sprints.")

        with st.expander("Demo data"):
            st.caption("Fake transactions for testing, only in your account.")
            if st.button("Add 30 demo expenses", use_container_width=True):
                tx.load_demo_data(conn, user["id"])
                st.rerun()
            if st.button("Remove demo expenses", use_container_width=True):
                tx.clear_demo_data(conn, user["id"])
                st.rerun()

        st.markdown(f"<div class='sc-user'>Logged in as <b>{theme.escape(user['username'])}</b></div>",
                    unsafe_allow_html=True)
        st.button("Log out", on_click=log_out, use_container_width=True)
        st.markdown(theme.PRIVACY, unsafe_allow_html=True)

    if st.session_state.page == "Add transaction":
        add_page(user["id"])
    else:
        transactions_page(user["id"])


user = st.session_state.get("user")
if user:
    main_app(user)
else:
    auth_page()
