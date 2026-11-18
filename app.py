"""SmartCash app. Run with:  streamlit run app.py

SCG-75 Log in / sign up        -> each user only sees their own data
SCG-31 Add expense, SCG-33 View and filter
SCG-28 Daily USD/KHR rate
Look: docs/design/smartcash-ui-design.pdf
"""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

# Must run BEFORE the other smartcash imports: after a git push, reload any
# smartcash file that changed, so new app.py never runs with old module code.
from smartcash import freshness
freshness.reload_if_changed()

from smartcash import auth, db, rates
from smartcash import diary_import
from smartcash import transactions as tx
from smartcash.ui import charts, theme

st.set_page_config(page_title="SmartCash", page_icon="💵", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(theme.CSS, unsafe_allow_html=True)

conn = db.connect()

PAGES = ["Overview", "Transactions", "Budgets", "Forecast", "Study Insights",
         "Add transaction", "Import diary"]
st.session_state.setdefault("page", "Transactions")


def go_to_add():
    st.session_state.page = "Add transaction"


# Page changes must happen in callbacks (they run BEFORE the menu is drawn).
# Setting st.session_state.page after the menu exists crashes Streamlit.
def start_edit(tx_id):
    st.session_state.edit_id = tx_id
    st.session_state.pop("delete_id", None)


def stop_edit():
    st.session_state.pop("edit_id", None)


def ask_delete(tx_id):
    st.session_state.delete_id = tx_id


def cancel_delete():
    st.session_state.pop("delete_id", None)


def confirm_delete(tx_id, label):
    # Only remember the choice here. The delete itself runs in the page code below,
    # because a callback must not use the database connection from the previous run
    # (SQLite only allows a connection in the thread that made it).
    st.session_state.pop("delete_id", None)
    st.session_state.do_delete = (tx_id, label)


def run_pending_delete(user_id):
    pending = st.session_state.pop("do_delete", None)
    if pending:
        tx_id, label = pending
        tx.delete_transaction(conn, user_id, tx_id)
        st.session_state.flash = f"Deleted {label}."


def on_menu_change():
    # Picking a page in the menu always leaves the edit screen and any open delete question.
    st.session_state.pop("edit_id", None)
    st.session_state.pop("delete_id", None)


def show_flash():
    msg = st.session_state.pop("flash", None)
    if msg:
        st.success(msg.replace("$", "\\$"))


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
    run_pending_delete(user_id)
    show_flash()
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
    net = income - spend
    today_rate = rates.rate_used(date.today())

    st.markdown(theme.cards([
        ("Income", f"${income:,.2f}", "USD equivalent", theme.GREEN),
        ("Spending", f"${spend:,.2f}", "USD equivalent", theme.AMBER),
        ("Net", f"{'-' if net < 0 else ''}${abs(net):,.2f}", "income minus spending", theme.BLUE),
        ("Rate used today", f"{today_rate.khr_per_usd:,.0f}",
         "KHR = $1 · NBC" + (" (earlier day)" if today_rate.filled else ""), theme.TEAL),
    ]), unsafe_allow_html=True)
    st.caption(f"{len(df)} transactions in this view.")

    st.markdown(theme.tx_table(rows), unsafe_allow_html=True)
    st.divider()
    st.subheader("Manage transactions")
    for row in rows:
        label = (f"{row['tx_date']} · {row['tx_type'].capitalize()} · {row['category']} · "
                 f"{theme.money(row['amount'], row['currency'])}")
        left, middle, edit, delete = st.columns([4, 2, 1, 1], vertical_alignment="center")
        left.write(f"{row['tx_date']} · {row['tx_type'].capitalize()} · {row['category']}")
        middle.write(theme.money(row["amount"], row["currency"]))
        edit.button("Edit", key=f"edit-{row['id']}", on_click=start_edit, args=(row["id"],))
        delete.button("Delete", key=f"delete-{row['id']}", on_click=ask_delete, args=(row["id"],))
        if st.session_state.get("delete_id") == row["id"]:
            # Ask right under the row the user clicked, not at the bottom of the list.
            with st.container(border=True):
                st.warning(f"Delete {label}? This can't be undone.")
                yes, no, _ = st.columns([1, 1, 4])
                yes.button("Yes, delete", type="primary", key=f"yes-{row['id']}",
                           on_click=confirm_delete, args=(row["id"], label))
                no.button("Cancel", key=f"no-{row['id']}", on_click=cancel_delete)

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
            payment = c5.selectbox("Received as" if tx_type == "income" else "Paid with",
                                   tx.PAYMENT_METHODS)
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
    tx_id = st.session_state.get("edit_id")
    row = next((r for r in rows if r["id"] == tx_id), None)
    st.button("← Back to transactions", on_click=stop_edit)
    if row is None:
        st.error("Transaction was not found. It may have been deleted.")
        return
    st.title("Edit transaction")
    st.caption("Change any field, then save. The same checks as Add are used.")
    k = f"edit-{tx_id}"   # keys per row, so editing another row starts fresh
    with st.container(border=True):
        tx_type = st.radio("Transaction type", ["expense", "income"], key=f"{k}-type",
                           index=0 if row["tx_type"] == "expense" else 1,
                           format_func=str.capitalize, horizontal=True)
        c1, c2 = st.columns(2)
        currency = c1.radio("Currency", tx.CURRENCIES, key=f"{k}-cur",
                            index=tx.CURRENCIES.index(row["currency"]), horizontal=True)
        tx_date = c2.date_input("Date", date.fromisoformat(row["tx_date"]),
                                max_value=date.today(), key=f"{k}-date")
        categories = tx.INCOME_CATEGORIES if tx_type == "income" else tx.EXPENSE_CATEGORIES
        with st.form(f"{k}-form", border=False):
            c3, c4 = st.columns(2)
            amount = c3.number_input(
                f"Amount ({currency})", min_value=0.0, value=float(row["amount"]),
                step=0.25 if currency == "USD" else 500.0,
                format="%.2f" if currency == "USD" else "%.0f")
            category = c4.selectbox(
                "Income source" if tx_type == "income" else "Category", categories,
                index=categories.index(row["category"]) if row["category"] in categories else 0)
            c5, c6 = st.columns(2)
            payment = c5.selectbox(
                "Received as" if tx_type == "income" else "Paid with", tx.PAYMENT_METHODS,
                index=(tx.PAYMENT_METHODS.index(row["payment_method"])
                       if row["payment_method"] in tx.PAYMENT_METHODS else 0))
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
            st.session_state.flash = (f"Updated: {tx_date} · {tx_type.capitalize()} · {category} · "
                                      f"{theme.money(amount, currency)}.")
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
    date_labels = {'%Y-%m-%d': 'Year-month-day (2026-11-18)',
                   '%d/%m/%Y': 'Day/month/year (18/11/2026)',
                   '%m/%d/%Y': 'Month/day/year (11/18/2026)'}
    date_format = st.selectbox('Date format in your file', list(date_labels),
                               format_func=date_labels.get)
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
    st.markdown(theme.cards([
        ("Balance", f"{'-' if balance < 0 else ''}${abs(balance):,.2f}", "income minus spending", theme.BLUE),
        ("Spent", f"${expenses:,.2f}", "USD, last 30 days", theme.AMBER),
        ("Income", f"${income:,.2f}", "recorded income", theme.GREEN),
        ("Transactions", str(len(rows)), "last 30 days", theme.TEAL),
    ]), unsafe_allow_html=True)
    left, right = st.columns([1.2, 1])
    with left:
        week_rows = _prepared_rows(user_id, charts.week_start(date.today()) - timedelta(weeks=8),
                                   date.today())
        weekly, so_far = charts.weekly_totals(week_rows, weeks=8)
        if weekly.usd.sum() == 0:
            st.info("Add or import transactions to see your weekly spending.")
        else:
            weekly = charts.trim_leading_empty_weeks(weekly)
            st.altair_chart(charts.weekly_spending_chart(weekly), use_container_width=True)
            st.caption(f"This week so far: \\${so_far:,.2f} (added to the chart when the week ends).")
            with st.expander("Show data"):
                st.dataframe(weekly[["week_label", "usd"]].rename(
                    columns={"week_label": "Week", "usd": "Spent (USD)"}), hide_index=True)
    with right:
        top = charts.category_totals(rows, top=5)
        if top.empty:
            st.info("Category insights will appear here.")
        else:
            st.altair_chart(charts.category_bars_chart(top, "Top categories",
                                                       "USD spent, last 30 days"),
                            use_container_width=True)
            with st.expander("Show data"):
                st.dataframe(top.rename(columns={"category": "Category", "usd": "Spent (USD)"}),
                             hide_index=True)


def budgets_page(user_id):
    """Budget screen matching the prototype with local budget limits."""
    st.title("Monthly budgets")
    st.caption("Set limits by category and see what is left this month (USD).")
    st.caption("Budgets are kept until you log out. Saving them for good comes with the Budgets story.")
    # Must be real category names, or the spending never matches and shows $0.
    defaults = {"Food & drinks": 120, "Transport": 45,
                "Shopping & personal care": 30, "Entertainment & social": 35}
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
            f"**{category}** — \\${amount:,.2f} of \\${limit:,.2f}<br>"
            f"<div class='sc-budget-track'><div class='sc-budget-fill {colour}' "
            f"style='width:{ratio * 100:.0f}%'></div></div>"
            f"<span class='sc-budget-status {colour}'>{status}</span>",
            unsafe_allow_html=True)
        st.write("")


def forecast_page(user_id):
    """Transparent forecast based on the trailing four weekly totals."""
    st.title("Next week forecast")
    st.caption("An estimate based on your last 4 full weeks — not a promise.")
    rows = _prepared_rows(user_id, charts.week_start(date.today()) - timedelta(weeks=8),
                          date.today())
    weekly, so_far = charts.weekly_totals(rows, weeks=8)
    fc = charts.forecast(weekly)
    if fc is None:
        st.info("Add at least one full week of spending to get a forecast.")
        return
    st.markdown(theme.cards([
        ("Likely spending", f"${fc['estimate']:,.2f}", "average of last 4 full weeks", theme.BLUE),
        ("Likely range", f"${fc['low']:,.0f} - ${fc['high']:,.0f}",
         "lowest to highest recent week", theme.TEAL),
        ("This week so far", f"${so_far:,.2f}", "week not finished", theme.AMBER),
    ]), unsafe_allow_html=True)
    st.altair_chart(charts.forecast_chart(charts.trim_leading_empty_weeks(weekly), fc),
                    use_container_width=True)
    with st.expander("Show data"):
        st.dataframe(weekly[["week_label", "usd"]].rename(
            columns={"week_label": "Week", "usd": "Spent (USD)"}), hide_index=True)


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
    all_cats = charts.category_totals(rows)
    st.altair_chart(charts.category_bars_chart(all_cats, "Spending by category",
                                               "USD, all time, biggest first"),
                    use_container_width=True)
    with st.expander("Show data"):
        st.dataframe(all_cats.rename(columns={"category": "Category", "usd": "Spent (USD)"}),
                     hide_index=True)


# ---------------- Main app (logged in) ----------------
def main_app(user):
    st.markdown(theme.TOPBAR, unsafe_allow_html=True)
    with st.sidebar:
        st.caption("WORKSPACE")
        st.radio("Menu", PAGES, key="page", label_visibility="collapsed",
                 on_change=on_menu_change)
        st.caption("Your money workspace")

        with st.expander("Demo data"):
            st.caption("Fake transactions for testing, only in your account.")
            if st.button(f"Add demo data ({tx.DEMO_EXPENSES} expenses + {tx.DEMO_INCOME} income)",
                         key="add-demo", use_container_width=True):
                tx.reset_demo_data(conn, user["id"])   # replaces old demo rows, never stacks them
                st.rerun()
            if st.button("Remove demo data", use_container_width=True):
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
