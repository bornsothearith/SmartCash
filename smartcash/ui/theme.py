"""SmartCash look and feel (matches docs/design/smartcash-ui-design.pdf).

Small HTML helpers so app.py stays short. All text is escaped.
"""
from html import escape

NAVY, BLUE, TEAL = "#16233F", "#2563EB", "#0F9E99"
GREEN, AMBER, RED = "#18803D", "#B45309", "#C2413B"
MUTED, BORDER, SOFT = "#64748B", "#E2E8F0", "#F6F8FB"

CSS = f"""
<style>
:root {{ --navy:{NAVY}; --blue:{BLUE}; --teal:{TEAL}; --green:{GREEN};
        --amber:{AMBER}; --red:{RED}; --muted:{MUTED}; --border:{BORDER}; }}
.block-container {{ padding-top: 2.2rem; max-width: 1150px; }}
h1, h2, h3 {{ color: var(--navy); letter-spacing: -0.01em; }}
section[data-testid="stSidebar"] {{ background: {SOFT}; border-right: 1px solid var(--border); }}

/* brand */
.sc-brand {{ display:flex; gap:.7rem; align-items:center; margin-bottom: 1.2rem; }}
.sc-logo {{ width:36px; height:36px; border-radius:50%; background:var(--teal); color:#fff;
           display:flex; align-items:center; justify-content:center; font-weight:700; font-size:1.1rem; }}
.sc-brand b {{ color:var(--navy); font-size:1.05rem; letter-spacing:.04em; }}
.sc-brand small {{ display:block; color:var(--muted); font-size:.78rem; }}

/* sidebar nav: radio styled as a menu */
section[data-testid="stSidebar"] div[role="radiogroup"] label {{
  padding:.55rem .75rem; border-radius:10px; margin-bottom:.15rem; width:100%; }}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
  background:#E8EEF6; font-weight:600; }}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div > div:first-child {{ display:none; }}

.sc-privacy {{ border-top:1px solid var(--border); padding-top:.8rem; margin-top:1rem;
              font-size:.8rem; color:var(--muted); }}
.sc-privacy b {{ color:var(--teal); display:block; margin-bottom:.15rem; }}

/* cards */
.sc-cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
            gap:1rem; margin:.4rem 0 1.2rem; }}
.sc-card {{ border:1px solid var(--border); border-radius:14px; padding:.9rem 1.1rem;
           border-top:5px solid var(--c); background:#fff; }}
.sc-card .lbl {{ color:var(--muted); font-size:.82rem; font-weight:600; }}
.sc-card .val {{ color:var(--navy); font-size:1.75rem; font-weight:700; line-height:1.3; }}
.sc-card .sub {{ color:var(--c); font-size:.78rem; font-weight:600; }}

/* table */
.sc-table-wrap {{ border:1px solid var(--border); border-radius:14px; padding:.4rem 1rem;
                 overflow-x:auto; background:#fff; }}
table.sc-table {{ width:100%; border-collapse:collapse; font-size:.9rem; border:none; }}
table.sc-table th, table.sc-table td {{ border-left:none !important; border-right:none !important;
                                       border-bottom:none !important; background:none; }}
table.sc-table th {{ border-top:none !important; }}
table.sc-table th {{ text-align:left; color:var(--muted); font-size:.72rem; font-weight:700;
                    text-transform:uppercase; letter-spacing:.04em; padding:.7rem .5rem; }}
table.sc-table td {{ padding:.7rem .5rem; border-top:1px solid var(--border); color:var(--navy); }}
table.sc-table td.num {{ text-align:right; white-space:nowrap; }}
table.sc-table th.num {{ text-align:right; }}
.sc-income {{ color:var(--green); font-weight:700; }}
.sc-rate {{ color:var(--muted); font-size:.78rem; }}

.sc-user {{ border-top:1px solid var(--border); padding-top:.8rem; margin:1rem 0 .4rem;
           font-size:.85rem; color:var(--muted); }}
.sc-user b {{ color:var(--navy); }}
.sc-note {{ background:#E9F6F5; border:1px solid #BFE5E2; border-radius:12px;
           padding:.7rem 1rem; color:var(--navy); font-size:.9rem; }}
.sc-note b {{ color:var(--teal); margin-right:.5rem; }}
</style>
"""

BRAND = """
<div class="sc-brand"><div class="sc-logo">$</div>
<div><b>SMARTCASH</b><small>Personal finance, made clear</small></div></div>
"""

PRIVACY = """
<div class="sc-privacy"><b>Privacy first</b>
No names or account numbers. Demo data is fake and never mixed with real diary data.</div>
"""


def cards(items):
    """items: list of (label, value, sub, colour)."""
    html = "".join(
        f'<div class="sc-card" style="--c:{c}"><div class="lbl">{escape(l)}</div>'
        f'<div class="val">{escape(v)}</div><div class="sub">{escape(s)}</div></div>'
        for l, v, s, c in items)
    return f'<div class="sc-cards">{html}</div>'


def money(amount, currency):
    return f"{amount:,.2f} USD" if currency == "USD" else f"{amount:,.0f} KHR"


def rate_text(rate):
    """'4,067 KHR = $1' plus a note when an earlier day's rate is used."""
    text = f"{rate.khr_per_usd:,.0f} KHR = $1"
    if rate.filled:
        text += f" (from {rate.rate_date:%d %b})"
    return text


def tx_table(rows):
    """rows: dicts with tx_date, tx_type, category, payment_method, amount,
    currency, usd, rate (RateUsed or None), note."""
    head = ("<tr><th>Date</th><th>Type</th><th>Category</th><th>Payment</th>"
            "<th class='num'>Amount</th><th class='num'>USD</th><th>Note</th></tr>")
    body = []
    for r in rows:
        kind = r["tx_type"].capitalize()
        kind_html = f"<span class='sc-income'>{kind}</span>" if kind == "Income" else kind
        usd = f"${r['usd']:,.2f}"
        if r["currency"] == "KHR" and r.get("rate"):
            usd += f"<br><span class='sc-rate'>{escape(rate_text(r['rate']))}</span>"
        body.append(
            f"<tr><td>{escape(r['tx_date'])}</td><td>{kind_html}</td>"
            f"<td>{escape(r['category'])}</td><td>{escape(r['payment_method'])}</td>"
            f"<td class='num'>{escape(money(r['amount'], r['currency']))}</td>"
            f"<td class='num'>{usd}</td><td>{escape(r.get('note') or '')}</td></tr>")
    return (f"<div class='sc-table-wrap'><table class='sc-table'>{head}"
            f"{''.join(body)}</table></div>")
