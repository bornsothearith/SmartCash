"""SmartCash look and feel (matches docs/design/smartcash-ui-design.pdf).

Small HTML helpers so app.py stays short. All text is escaped.
"""
from html import escape

NAVY, BLUE, TEAL = "#192B46", "#306BEA", "#17A6A4"
PURPLE = "#843DF2"
GREEN, AMBER, RED = "#19844A", "#BF6007", "#C64141"
MUTED, BORDER, SOFT = "#78869A", "#E3E8EE", "#F5F7FA"

CSS = f"""
<style>
:root {{ --navy:{NAVY}; --blue:{BLUE}; --teal:{TEAL}; --green:{GREEN};
        --amber:{AMBER}; --red:{RED}; --muted:{MUTED}; --border:{BORDER}; }}
html, body, [data-testid="stAppViewContainer"] {{ background:#fff; color:var(--navy); }}
body, .stApp {{ font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
#MainMenu, footer, header[data-testid="stHeader"], div[data-testid="stToolbar"] {{ display:none !important; }}
.block-container {{ padding: 2.2rem 1.5rem 3.5rem; max-width: 1080px; }}
h1, h2, h3 {{ color: var(--navy); letter-spacing: -0.02em; }}
h1 {{ font-size:2rem; font-weight:800; }}
h2 {{ font-size:1.45rem; font-weight:800; }}
h3 {{ font-size:1rem; font-weight:750; }}
section[data-testid="stSidebar"] {{ background:#fff; border-right:0; }}
section[data-testid="stSidebar"] > div {{ padding:1rem .8rem; }}
div[data-testid="stSidebarContent"] {{ background:{SOFT}; border:1px solid var(--border);
  border-radius:16px; margin:1rem .55rem; padding:1.25rem .7rem; min-height:calc(100vh - 2rem); }}

/* brand */
.sc-brand {{ display:flex; gap:.7rem; align-items:center; margin-bottom: 1.2rem; }}
.sc-logo {{ width:36px; height:36px; border-radius:50%; background:var(--teal); color:#fff;
           display:flex; align-items:center; justify-content:center; font-weight:700; font-size:1.1rem; }}
.sc-brand b {{ color:var(--navy); font-size:1.05rem; letter-spacing:.04em; }}
.sc-brand small {{ display:block; color:var(--muted); font-size:.78rem; }}

/* sidebar nav: radio styled as a menu */
section[data-testid="stSidebar"] div[role="radiogroup"] label {{
  padding:.62rem .75rem; border-radius:9px; margin-bottom:.15rem; width:100%;
  color:#7A8A9F; font-size:.82rem; }}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
  background:#E7EEF7; color:var(--navy); font-weight:750; }}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div > div:first-child {{ display:none; }}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color:#8290A2; }}

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
.sc-budget-track {{ height:14px; background:#EAF0F7; border-radius:9px; overflow:hidden;
  margin:.45rem 0 .35rem; max-width:100%; }}
.sc-budget-fill {{ height:100%; border-radius:9px; background:var(--green); }}
.sc-budget-fill.orange {{ background:var(--amber); }}
.sc-budget-fill.red {{ background:var(--red); }}
.sc-budget-status {{ display:inline-block; color:#fff; background:var(--green);
  border-radius:9px; padding:.25rem .55rem; font-size:.7rem; font-weight:750; }}
.sc-budget-status.orange {{ background:var(--amber); }}
.sc-budget-status.red {{ background:var(--red); }}

/* Streamlit controls styled like the prototype fields and buttons */
div[data-testid="stButton"] > button, div[data-testid="stDownloadButton"] > button,
div[data-testid="stFormSubmitButton"] > button {{ border-radius:8px; min-height:40px;
  font-weight:700; border:1px solid var(--border); color:#334962; background:#fff; }}
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stFormSubmitButton"] > button[kind="primary"] {{ background:var(--blue);
  color:#fff; border-color:var(--blue); }}
div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input,
div[data-testid="stDateInput"] input, div[data-testid="stFileUploader"] section,
div[data-testid="stMultiSelect"] > div, div[data-testid="stSelectbox"] > div {{
  border-color:#DCE3ED; border-radius:9px; background:#F9FAFC; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{ border-color:var(--border); border-radius:12px; }}
div[data-testid="stAlert"] {{ border-radius:10px; }}

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

/* Responsive prototype shell */
.sc-topbar {{ height:76px; border-bottom:1px solid var(--border); display:flex;
              align-items:center; justify-content:space-between; padding:0 30px;
              gap:22px; background:#fff; margin:-2.2rem -1rem 1.2rem; }}
.sc-topbrand {{ display:flex; align-items:center; gap:.65rem; min-width:220px; }}
.sc-topbrand .sc-logo {{ width:34px; height:34px; background:var(--blue); }}
.sc-topbrand strong {{ color:var(--navy); font-size:.9rem; letter-spacing:.08em; }}
.sc-topbrand small {{ display:block; color:var(--muted); font-size:.72rem; margin-top:.1rem; }}
.sc-topcenter {{ text-align:center; flex:1; color:var(--navy); }}
.sc-topcenter strong {{ display:block; font-size:1rem; }}
.sc-topcenter span {{ color:var(--muted); font-size:.78rem; }}
.sc-pagecount {{ color:var(--muted); font-size:.78rem; white-space:nowrap; }}
section[data-testid="stSidebar"] {{ background:#fff; border-right:0; }}
section[data-testid="stSidebar"] > div {{ padding:1rem .8rem; }}
section[data-testid="stSidebar"] .block-container {{ background:var(--soft); border-radius:14px;
  padding:1rem .85rem; min-height:calc(100vh - 2rem); }}
button {{ border-radius:8px !important; }}
div[data-testid="stMetric"] {{ border:1px solid var(--border); border-radius:12px;
  padding:.8rem 1rem; background:#fff; }}
div[data-testid="stExpander"] {{ border:1px solid var(--border); border-radius:12px; }}
@media (max-width:750px) {{
  .sc-topbar {{ height:64px; margin:-1rem -.5rem 1rem; padding:0 14px; }}
  .sc-topcenter, .sc-pagecount {{ display:none; }}
  .sc-topbrand {{ min-width:0; }}
  .block-container {{ padding-top:1rem; }}
}}
</style>
"""

TOPBAR = """
<div class="sc-topbar">
  <div class="sc-topbrand">
    <div class="sc-logo">$</div>
    <div><strong>SMARTCASH</strong><small>Personal finance, made clear</small></div>
  </div>
  <div class="sc-topcenter"><strong>SmartCash</strong>
    <span>Track income and spending in USD and KHR</span></div>
</div>
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
