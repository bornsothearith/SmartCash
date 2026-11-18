"""SmartCash app. Run with:  streamlit run app.py

SCG-75 Log in / sign up        -> each user only sees their own data
SCG-31 Add expense, SCG-33 View and filter
SCG-28 Daily USD/KHR rate
Look: docs/design/smartcash-ui-design.pdf
"""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from smartcash import auth, db, rates
from smartcash import diary_import
from smartcash import transactions as tx
from smartcash.ui import theme

st.set_page_config(page_title="SmartCash", page_icon="💵", layout="wide")
st.markdown(theme.CSS, unsafe_allow_html=True)

conn = db.connect()

PAGES = ["Overview", "Transactions", "Budgets", "Forecast", "Study Insights",
         "Add transaction", "Import diary"]
st.session_state.setdefault("page", "Transactions")


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
    h1.caption("Review, filter, and manage income and expenses.")
    h2.button("+ Add transaction", type="primary", on_click=go_to_add,
              use_container_width=True)

    with st.container(border=True):
        f1, f2, f3 = st.columns([2, 2, 1])
        default_start = date.today() - timedelta(days=30)
        period = f1.date_input("Dates", value=(default_start, date.today()))
        cats = f2.multiselect("Category", sorted(set(tx.EXPENSE_CATEGORIES + tx.INCOME_CATEGORIES)),
                              placeholder="All categories")
        types = f3.multiselect("Type", ["expense", "income"], placeholder="All")

    start, end = (period if isinstance(period, tuple) and len(period) == 2
                  else (period[0] if isinstance(period, tuple) else period, None))
    rows = tx.filter_transactions(conn, user_id, start, end, cats, types)

    if not rows:
        st.info("No transactions match these filters. Add a transaction or import a diary.")
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
    st.divider()
    st.subheader("Manage transactions")
    for row in rows:
        left, middle, edit, delete = st.columns([4, 2, 1, 1])
        left.write(f"{row['tx_date']} · {row['tx_type'].capitalize()} · {row['category']}")
        middle.write(theme.money(row["amount"], row["currency"]))
        if edit.button("Edit", key=f"edit-{row['id']}"):
            st.session_state.edit_id = row["id"]
            st.session_state.page = "Transactions"
            st.rerun()
        if delete.button("Delete", key=f"delete-{row['id']}"):
            st.session_state.delete_id = row["id"]
            st.session_state.confirm_delete = True
            st.rerun()

    if st.session_state.get("confirm_delete"):
        delete_id = st.session_state.get("delete_id")
        st.warning("Delete this transaction permanently?")
        yes, no = st.columns(2)
        if yes.button("Yes, delete", type="primary"):
            tx.delete_transaction(conn, user_id, delete_id)
            st.session_state.pop("delete_id", None)
            st.session_state.pop("confirm_delete", None)
            st.rerun()
        if no.button("Cancel"):
            st.session_state.pop("delete_id", None)
            st.session_state.pop("confirm_delete", None)
            st.rerun()
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
        tx_type = st.radio("Transaction type", ["expense", "income"],
                           format_func=str.capitalize, horizontal=True)
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
            category_options = (tx.INCOME_CATEGORIES if tx_type == "income"
                                else tx.EXPENSE_CATEGORIES)
            category = c4.selectbox("Income source" if tx_type == "income" else "Category",
                                    category_options)
            c5, c6 = st.columns(2)
            payment = c5.selectbox("Paid with", tx.PAYMENT_METHODS)
            note = c6.text_input("Note (optional)", max_chars=200,
                                 placeholder="e.g. lunch near campus")
            saved = st.form_submit_button("Save transaction", type="primary")

    if saved:
        transaction = tx.Transaction(tx_date, tx_type, amount, currency, category, payment, note)
        problems = tx.validate_transaction(transaction)
        if problems:
            for p in problems:
                st.error(p)
        else:
            tx.add_transaction(conn, user_id, transaction)
            shown = theme.money(amount, currency)
            if currency == "KHR":
                shown += f" (≈ ${tx.to_usd(amount, currency, tx_date):,.2f} at {theme.rate_text(rate)})"
            # "\$" so Streamlit doesn't read "$...$" as a maths formula
            st.success(f"Saved: {shown} on {category}.".replace("$", "\\$"))


def edit_page(user_id):
    rows = tx.filter_transactions(conn, user_id)
    row = next((r for r in rows if r["id"] == st.session_state.get("edit_id")), None)
    if row is None:
        st.error("Transaction was not found.")
        return
    st.title("Edit transaction")
    tx_type = st.radio("Transaction type", ["expense", "income"],
                       index=0 if row["tx_type"] == "expense" else 1,
                       format_func=str.capitalize, horizontal=True)
    categories = tx.INCOME_CATEGORIES if tx_type == "income" else tx.EXPENSE_CATEGORIES
    with st.form("edit_transaction"):
        c1, c2 = st.columns(2)
        tx_date = c1.date_input("Date", date.fromisoformat(row["tx_date"]), max_value=date.today())
        currency = c2.radio("Currency", tx.CURRENCIES,
                            index=tx.CURRENCIES.index(row["currency"]), horizontal=True)
        c3, c4 = st.columns(2)
        amount = c3.number_input("Amount", min_value=0.0, value=float(row["amount"]),
                                 step=0.25 if currency == "USD" else 500.0)
        category = c4.selectbox("Income source" if tx_type == "income" else "Category",
                                categories, index=categories.index(row["category"]) if row["category"] in categories else 0)
        c5, c6 = st.columns(2)
        payment = c5.selectbox("Paid with", tx.PAYMENT_METHODS,
                               index=tx.PAYMENT_METHODS.index(row["payment_method"]) if row["payment_method"] in tx.PAYMENT_METHODS else 0)
        note = c6.text_input("Note (optional)", value=row.get("note") or "", max_chars=200)
        saved = st.form_submit_button("Save changes", type="primary")
    if saved:
        updated = tx.Transaction(tx_date, tx_type, amount, currency, category, payment, note)
        problems = tx.validate_transaction(updated)
        if problems:
            for problem in problems:
                st.error(problem)
        else:
            tx.update_transaction(conn, user_id, row["id"], updated)
            st.success("Transaction updated.")
            st.session_state.page = "Transactions"
            st.session_state.pop("edit_id", None)
            st.rerun()


def import_page(user_id):
    st.title("Import diary")
    st.caption("Upload a CSV exported from the spending diary or Google Form.")
    st.code("tx_date,tx_type,amount,currency,category,payment_method,note,is_demo")
    uploaded = st.file_uploader("Choose a diary CSV", type="csv")
    if not uploaded:
        return
    try:
        uploaded.seek(0)
        headers = diary_import.read_csv(uploaded).fieldnames or []
    except (UnicodeError, ValueError, diary_import.csv.Error) as exc:
        st.error(f"Cannot read CSV: {exc}")
        return
    st.caption("Map your CSV or Google Form headings. Unmapped columns remain in private raw storage; do not upload names or bank details.")
    fields = ['Ignore'] + list(diary_import.CSV_COLUMNS) + ['is_demo', 'source']
    suggested = diary_import.suggested_mapping(headers)
    mapping = {}
    for i, header in enumerate(headers):
        guess = suggested.get(header)
        choice = st.selectbox(header, fields, index=fields.index(guess) if guess in fields else 0,
                              key=f'import-column-{i}-{header}')
        mapping[header] = None if choice == 'Ignore' else choice
    date_format = st.selectbox('Date format', ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'])
    if st.button("Import CSV", type="primary"):
        uploaded.seek(0)
        try:
            result = diary_import.import_csv(conn, user_id, uploaded, mapping, date_format)
        except (ValueError, UnicodeError, diary_import.csv.Error) as exc:
            st.error(f"Import stopped: {exc}. Earlier processed rows may have been saved.")
            return
        st.success(f"Read {result['read']} rows. Imported {result['imported']}. Skipped {result['duplicates']} duplicates. Rejected {len(result['rejected'])}.")
        if result["rejected"]:
            st.error(f"Rejected {len(result['rejected'])} rows.")
            st.dataframe(pd.DataFrame(result["rejected"]), use_container_width=True)


def _prepared_rows(user_id, start=None, end=None):
    """Return this user's rows with a USD value for dashboard screens."""
    rows = tx.filter_transactions(conn, user_id, start, end)
    for row in rows:
        row["usd"] = tx.to_usd(row["amount"], row["currency"], row["tx_date"])
    return rows


def overview_page(user_id):
    """Prototype overview dashboard backed by the user's transactions."""
    st.title("Overview")
    st.caption("Your money picture for the last 30 days.")
    rows = _prepared_rows(user_id, date.today() - timedelta(days=30), date.today())
    df = pd.DataFrame(rows)
    expenses = df.loc[df.tx_type == "expense", "usd"].sum() if not df.empty else 0
    income = df.loc[df.tx_type == "income", "usd"].sum() if not df.empty else 0
    balance = income - expenses
    categories = (df.loc[df.tx_type == "expense"].groupby("category")["usd"]
                  .sum().sort_values(ascending=False) if not df.empty else pd.Series(dtype=float))
    st.markdown(theme.cards([
        ("Balance", f"${balance:,.2f}", "income minus spending", theme.BLUE),
        ("Spent this month", f"${expenses:,.2f}", "USD equivalent", theme.AMBER),
        ("Income", f"${income:,.2f}", "recorded income", theme.GREEN),
        ("Transactions", str(len(rows)), "last 30 days", theme.TEAL),
    ]), unsafe_allow_html=True)
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Weekly spending")
        if df.empty or not (df.tx_type == "expense").any():
            st.info("Add or import transactions to see the spending chart.")
        else:
            chart = df[df.tx_type == "expense"].copy()
            chart["week"] = pd.to_datetime(chart["tx_date"]).dt.to_period("W").astype(str)
            st.bar_chart(chart.groupby("week")["usd"].sum())
    with right:
        st.subheader("Top categories")
        if categories.empty:
            st.info("Category insights will appear here.")
        else:
            st.bar_chart(categories.head(5))


def budgets_page(user_id):
    """Budget screen matching the prototype with local budget limits."""
    st.title("Monthly budgets")
    st.caption("Set limits by category and see what is left.")
    defaults = {"Food & drinks": 120, "Transport": 60, "Shopping": 100, "Bills": 80}
    budgets = st.session_state.setdefault("budgets", defaults.copy())
    with st.expander("Add or update a budget"):
        with st.form("budget_form"):
            category = st.selectbox("Category", tx.EXPENSE_CATEGORIES)
            limit = st.number_input("Monthly limit (USD)", min_value=1.0,
                                    value=float(budgets.get(category, 50.0)), step=5.0)
            saved = st.form_submit_button("Save budget", type="primary")
        if saved:
            budgets[category] = limit
            st.success(f"Budget saved for {category}.")
    rows = _prepared_rows(user_id, date.today().replace(day=1), date.today())
    spent = (pd.DataFrame(rows).query("tx_type == 'expense'").groupby("category")["usd"].sum()
             if rows else pd.Series(dtype=float))
    for category, limit in budgets.items():
        amount = float(spent.get(category, 0))
        ratio = min(amount / limit, 1.0) if limit else 0
        status = "Over budget" if amount > limit else ("Watch" if ratio >= .8 else "On track")
        colour = "red" if amount > limit else ("orange" if ratio >= .8 else "green")
        st.markdown(
            f"**{category}** — ${amount:,.2f} of ${limit:,.2f}<br>"
            f"<div class='sc-budget-track'><div class='sc-budget-fill {colour}' "
            f"style='width:{ratio * 100:.0f}%'></div></div>"
            f"<span class='sc-budget-status {colour}'>{status}</span>",
            unsafe_allow_html=True)
        st.write("")


def forecast_page(user_id):
    """Transparent forecast based on the trailing four weekly totals."""
    st.title("Next week forecast")
    st.caption("An estimate based on recent spending — not a promise.")
    rows = _prepared_rows(user_id, date.today() - timedelta(days=28), date.today())
    df = pd.DataFrame([r for r in rows if r["tx_type"] == "expense"])
    if df.empty:
        st.info("Add transactions to generate a forecast.")
        return
    df["week"] = pd.to_datetime(df["tx_date"]).dt.to_period("W").astype(str)
    weekly = df.groupby("week")["usd"].sum()
    average = float(weekly.tail(4).mean()) if not weekly.empty else 0
    st.markdown(theme.cards([
        ("Expected next week", f"${average:,.2f}", "4-week average", theme.BLUE),
        ("Likely low", f"${average * .85:,.2f}", "estimated range", theme.TEAL),
        ("Likely high", f"${average * 1.15:,.2f}", "estimated range", theme.AMBER),
    ]), unsafe_allow_html=True)
    st.subheader("Weekly spending and forecast")
    forecast = weekly.copy()
    forecast.loc["Next week"] = average
    st.line_chart(forecast)


def study_insights_page(user_id):
    """Anonymous-style aggregate view without individual participant records."""
    st.title("Study insights")
    st.caption("Anonymous and aggregated spending insights.")
    rows = _prepared_rows(user_id)
    df = pd.DataFrame([r for r in rows if r["tx_type"] == "expense"])
    st.markdown(
        "<div class='sc-note'><b>Privacy first</b> This view shows categories and totals only. "
        "It does not show names, account numbers, or individual participant records.</div>",
        unsafe_allow_html=True)
    if df.empty:
        st.info("Add or import transactions to see study insights.")
        return
    category_totals = df.groupby("category")["usd"].sum().sort_values(ascending=False)
    st.markdown(theme.cards([
        ("Total spending", f"${df.usd.sum():,.2f}", "aggregated USD", theme.BLUE),
        ("Top category", str(category_totals.index[0]), "highest total", theme.TEAL),
        ("Records analysed", str(len(df)), "expense records", theme.PURPLE),
    ]), unsafe_allow_html=True)
    st.subheader("Spending by category")
    st.bar_chart(category_totals)


# ---------------- Main app (logged in) ----------------
def main_app(user):
    st.markdown(theme.TOPBAR, unsafe_allow_html=True)
    with st.sidebar:
        st.caption("WORKSPACE")
        st.radio("Menu", PAGES, key="page", label_visibility="collapsed")
        st.caption("Your money workspace")

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

    if st.session_state.get("edit_id"):
        edit_page(user["id"])
    elif st.session_state.page == "Overview":
        overview_page(user["id"])
    elif st.session_state.page == "Budgets":
        budgets_page(user["id"])
    elif st.session_state.page == "Forecast":
        forecast_page(user["id"])
    elif st.session_state.page == "Study Insights":
        study_insights_page(user["id"])
    elif st.session_state.page == "Add transaction":
        add_page(user["id"])
    elif st.session_state.page == "Import diary":
        import_page(user["id"])
    else:
        transactions_page(user["id"])


user = st.session_state.get("user")
if user:
    main_app(user)
else:
    auth_page()
