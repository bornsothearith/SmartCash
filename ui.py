"""SmartCash UI helpers: the design system applied to Streamlit.

Colours, fonts and spacing come from design-system/ (tokens.css and
components/components.css). Don't hard-code new values here; use the tokens.

The formatting functions are plain Python so they can be tested without Streamlit.
"""
from html import escape
from pathlib import Path

DS = Path(__file__).parent / "design-system"
MINUS = "−"  # a real minus sign, not a hyphen

# Small additions for the transaction list. They only use design-system tokens.
_EXTRA_CSS = """
.sc-badge--income .sc-badge__dot { background: var(--success); }
.sc-badge--expense .sc-badge__dot { background: var(--danger); }
.sc-card { height: 100%; }
.sc-card .sc-amount--lg { display: block; margin: 0 0 var(--space-xs); }
.sc-tx { border: 1px solid var(--hairline); border-radius: var(--radius-lg); background: var(--canvas);
  overflow: auto; max-height: 560px; }
.sc-tx table { width: 100%; min-width: 640px; border-collapse: collapse; font-size: 14px; }
.sc-tx th { position: sticky; top: 0; background: var(--surface-1); color: var(--ink-subtle); font-size: 12px;
  font-weight: 500; text-align: left; padding: var(--space-xs) var(--space-md); border-bottom: 1px solid var(--hairline); }
.sc-tx td { padding: var(--space-xs) var(--space-md); border-bottom: 1px solid var(--hairline); color: var(--ink);
  border-top: 0; border-left: 0; border-right: 0; }
.sc-tx tr:last-child td { border-bottom: 0; }
.sc-tx tbody tr:hover td { background: var(--surface-1); }
.sc-tx__date { font-family: var(--font-mono); font-size: 13px; color: var(--ink-subtle); white-space: nowrap; }
.sc-tx__muted { color: var(--ink-muted); }
.sc-tx__note { color: var(--ink-subtle); max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sc-tx .sc-tx__num { text-align: right; white-space: nowrap; }
"""


# ---------------- formatting (pure Python) ----------------
def format_money(amount, currency, sign=None):
    """USD as $1,284.50 and KHR as ៛40,000 (whole riel).

    sign: None (no sign), "+" or "-". A negative amount always gets a minus.
    """
    if amount < 0:
        amount, sign = -amount, "-"
    text = f"${amount:,.2f}" if currency == "USD" else f"៛{amount:,.0f}"
    prefix = {"+": "+", "-": MINUS}.get(sign, "")
    return prefix + text


def amount_html(amount, currency, direction=None, large=False):
    """An sc-amount span. direction: "income", "expense" or None.

    Income gets +, expense gets −, so colour is never the only signal.
    """
    sign = {"income": "+", "expense": "-"}.get(direction)
    classes = ["sc-amount"]
    if direction in ("income", "expense"):
        classes.append(f"sc-amount--{direction}")
    if large:
        classes.append("sc-amount--lg")
    return f'<span class="{" ".join(classes)}">{escape(format_money(amount, currency, sign))}</span>'


def plural(n, one, many):
    return f"{n} {one if n == 1 else many}"


def net_direction(net):
    """Net above 0 reads as income, below 0 as spending, 0 stays neutral."""
    return "income" if net > 0 else "expense" if net < 0 else None


def summary_card(eyebrow, amount, direction, body, featured=False):
    """A Card holding one big USD amount (Income, Spending or Net)."""
    cls = "sc-card sc-card--featured" if featured else "sc-card"
    return (f'<div class="sc-root {cls}">'
            f'<p class="sc-card__eyebrow">{escape(eyebrow.upper())}</p>'
            f'{amount_html(abs(amount), "USD", direction, large=True)}'
            f'<p class="sc-card__body">{escape(body)}</p></div>')


def empty_card(title, body):
    return (f'<div class="sc-root sc-card"><p class="sc-card__title">{escape(title)}</p>'
            f'<p class="sc-card__body">{escape(body)}</p></div>')


def transactions_table(rows):
    """Dense transaction list. Every value from the database is escaped."""
    head = ("".join(f"<th>{h}</th>" for h in ["Date", "Type", "Category", "Paid with", "Note"])
            + '<th class="sc-tx__num">Amount</th>')
    body = []
    for r in rows:
        kind = r["tx_type"]
        label = "Income" if kind == "income" else "Expense"
        note = r.get("note") or ""
        body.append(
            "<tr>"
            f'<td class="sc-tx__date">{escape(r["tx_date"])}</td>'
            f'<td><span class="sc-badge sc-badge--{kind}"><span class="sc-badge__dot"></span>{label}</span></td>'
            f'<td>{escape(r["category"])}</td>'
            f'<td class="sc-tx__muted">{escape(r["payment_method"])}</td>'
            f'<td class="sc-tx__note" title="{escape(note)}">{escape(note)}</td>'
            f'<td class="sc-tx__num">{amount_html(r["amount"], r["currency"], kind)}</td>'
            "</tr>")
    return (f'<div class="sc-root sc-tx"><table><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


# ---------------- Streamlit ----------------
def inject_css():
    """Load the design-system CSS once per page run."""
    import streamlit as st
    # components.css starts with the font @import, which must come first.
    css = ((DS / "components" / "components.css").read_text(encoding="utf-8")
           + (DS / "tokens.css").read_text(encoding="utf-8") + _EXTRA_CSS)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def html(markup):
    import streamlit as st
    st.markdown(markup, unsafe_allow_html=True)
