"""Charts for SmartCash (Altair, which comes with Streamlit).

Rules we follow (see the dataviz guide):
- Pick the chart by its job: trend over time -> line, compare categories -> ranked bars.
- One series = one colour (blue). Two series = blue + teal (checked colour-blind safe),
  plus a second clue (dashed line) and a legend, so colour is never the only clue.
- Every chart has a title, a USD axis title and a hover tooltip.
- Thin marks, light solid gridlines, no dual axes.
- Only FULL weeks (Monday-Sunday) are drawn, so a half-finished week never looks like a drop.
"""
from datetime import date, timedelta

import altair as alt
import pandas as pd

from smartcash.ui.theme import BLUE, TEAL

INK, MUTED, GRID = "#192B46", "#64748B", "#E2E8F0"

# Each category ALWAYS has the same colour, in every chart (colour follows the category,
# never its rank). 8 validated colour-blind-safe hues in fixed order; the 3 rarer
# categories share a neutral grey. Bars are always labelled, so colour is never the only clue.
NEUTRAL = "#8A8A85"
CATEGORY_COLORS = {
    "Food & drinks": "#2a78d6",             # blue
    "Transport": "#eb6834",                 # orange
    "Groceries": "#1baf7a",                 # aqua
    "Phone & internet": "#eda100",          # yellow
    "Shopping & personal care": "#e87ba4",  # magenta
    "Education": "#008300",                 # green
    "Entertainment & social": "#6250d6",    # violet
    "Rent & utilities": "#e34948",          # red
    "Health": NEUTRAL,
    "Family, gifts & ceremonies": NEUTRAL,
    "Other": NEUTRAL,
}
FONT = "Source Sans Pro, sans-serif"


# ---------------- data helpers (pure pandas, easy to test) ----------------
def week_start(day):
    """Monday of the week that contains `day`."""
    return day - timedelta(days=day.weekday())


def weekly_totals(rows, weeks=8, today=None):
    """Spending (USD) per FULL week for the last `weeks` weeks.

    Returns (frame, this_week_so_far). Weeks with no spending are 0, not missing.
    The current, unfinished week is left out of the frame and returned separately.
    """
    today = today or date.today()
    this_week = week_start(today)
    starts = [this_week - timedelta(weeks=i) for i in range(weeks, 0, -1)]
    df = pd.DataFrame(rows)
    totals = {s: 0.0 for s in starts}
    so_far = 0.0
    if not df.empty:
        spend = df[df.tx_type == "expense"].copy()
        spend["week"] = [week_start(date.fromisoformat(d)) for d in spend.tx_date]
        by_week = spend.groupby("week")["usd"].sum()
        for s in starts:
            totals[s] = float(by_week.get(s, 0.0))
        so_far = float(by_week.get(this_week, 0.0))
    frame = pd.DataFrame({
        "week_start": pd.to_datetime(list(totals)),
        "usd": [round(v, 2) for v in totals.values()],
    })
    frame["week_label"] = [f"{d:%d %b} – {d + timedelta(days=6):%d %b}" for d in frame.week_start]
    return frame, round(so_far, 2)


def trim_leading_empty_weeks(weekly):
    """Drop the empty weeks before the first week with spending (for display only)."""
    nonzero = weekly.index[weekly.usd > 0]
    return weekly.loc[nonzero[0]:].reset_index(drop=True) if len(nonzero) else weekly


def category_totals(rows, top=None):
    """Spending (USD) per expense category, biggest first."""
    df = pd.DataFrame(rows)
    if df.empty or not (df.tx_type == "expense").any():
        return pd.DataFrame(columns=["category", "usd"])
    out = (df[df.tx_type == "expense"].groupby("category")["usd"].sum()
           .sort_values(ascending=False).round(2).reset_index())
    return out.head(top) if top else out


def forecast(weekly):
    """Next-week estimate from the last 4 full weeks.

    estimate = their average; likely range = their lowest to highest week.
    Returns None when there is no full week with spending yet.
    """
    recent = weekly.tail(4)
    if recent.empty or recent.usd.sum() == 0:
        return None
    return {"estimate": round(float(recent.usd.mean()), 2),
            "low": round(float(recent.usd.min()), 2),
            "high": round(float(recent.usd.max()), 2),
            "weeks_used": len(recent)}


# ---------------- charts ----------------
def _style(chart, title, subtitle=""):
    return (chart.properties(title=alt.TitleParams(title, subtitle=subtitle or None,
                                                   anchor="start", color=INK,
                                                   subtitleColor=MUTED, fontSize=15))
            .configure_axis(gridColor=GRID, domainColor=GRID, tickColor=GRID,
                            labelColor=MUTED, titleColor=MUTED, labelFont=FONT,
                            titleFont=FONT, titleFontWeight="normal")
            .configure_view(strokeWidth=0)
            .configure_legend(labelColor=INK, titleColor=MUTED, orient="top")
            .configure(font=FONT))


def _usd_axis(title="Spending (USD)"):
    return alt.Y("usd:Q", title=title, axis=alt.Axis(format="$,.0f", tickCount=5))


def _week_axis(order):
    """Exact week labels (e.g. '09 Nov'), in date order.

    A time axis would put its ticks on Sundays while our weeks start on Monday,
    so we use the real labels instead.
    """
    return alt.X("week_short:N", sort=order, title="Week starting",
                 scale=alt.Scale(domain=order),   # keep empty weeks (e.g. this week) on the axis
                 axis=alt.Axis(labelAngle=0, labelColor=MUTED, ticks=False))


def _short(frame):
    return frame.assign(week_short=[f"{d:%d %b}" for d in frame.week_start])


def weekly_spending_chart(weekly):
    """Trend over time -> one blue line with points, full weeks only."""
    weekly = _short(weekly)
    base = alt.Chart(weekly).encode(
        x=_week_axis(list(weekly.week_short)),
        y=_usd_axis(),
        tooltip=[alt.Tooltip("week_label:N", title="Week"),
                 alt.Tooltip("usd:Q", title="Spent (USD)", format="$,.2f")],
    )
    line = base.mark_line(color=BLUE, strokeWidth=2)
    points = base.mark_point(color=BLUE, filled=True, size=70)
    return _style((line + points).properties(height=260),
                  "Weekly spending", "USD, full weeks (Mon-Sun)")


def category_bars_chart(cats, title="Top categories", subtitle="USD spent, biggest first"):
    """Compare categories -> ranked horizontal bars in one colour, value at the end."""
    order = list(cats.category)
    base = alt.Chart(cats).encode(
        y=alt.Y("category:N", sort=order, title=None,
                axis=alt.Axis(labelLimit=180, labelColor=INK, ticks=False, domain=False)),
        x=alt.X("usd:Q", title="Spent (USD)", axis=alt.Axis(format="$,.0f", tickCount=4)),
        tooltip=[alt.Tooltip("category:N", title="Category"),
                 alt.Tooltip("usd:Q", title="Spent (USD)", format="$,.2f")],
    )
    names = list(CATEGORY_COLORS)
    bars = base.mark_bar(cornerRadiusEnd=4).encode(
        color=alt.Color("category:N", legend=None,   # the axis already names every bar
                        scale=alt.Scale(domain=names + ["(other)"],
                                        range=[CATEGORY_COLORS[n] for n in names] + [NEUTRAL])))
    labels = base.mark_text(align="left", dx=6, color=INK, fontSize=12).encode(
        text=alt.Text("usd:Q", format="$,.0f"))
    # Step = fixed height per bar, so bars never squash together.
    return _style((bars + labels).properties(height=alt.Step(34)), title, subtitle)


def forecast_chart(weekly, fc):
    """Actual full weeks (blue line) + next-week estimate (teal dot) inside its likely range (shaded).

    The current, unfinished week is shown as a gap labelled 'This week', so the
    estimate sits on the real next week and nothing is drawn for a half week.
    """
    weekly = _short(weekly)
    this_week = weekly.week_start.iloc[-1] + pd.Timedelta(days=7)
    next_week = this_week + pd.Timedelta(days=7)
    order = list(weekly.week_short) + [f"{this_week:%d %b}", f"{next_week:%d %b}"]
    nxt = order[-1]

    actual = weekly.assign(series="Actual")
    estimate = pd.DataFrame({"week_short": [nxt], "usd": [fc["estimate"]], "series": ["Estimate"],
                             "week_label": [f"Next week ({next_week:%d %b}), estimate"],
                             "low": [fc["low"]], "high": [fc["high"]]})
    colour = alt.Color("series:N", title=None,
                       scale=alt.Scale(domain=["Actual", "Estimate"], range=[BLUE, TEAL]),
                       legend=alt.Legend(orient="top", direction="horizontal", symbolType="circle"))
    x = _week_axis(order)
    tip = [alt.Tooltip("week_label:N", title="Week"),
           alt.Tooltip("usd:Q", title="USD", format="$,.2f")]

    shade = alt.Chart(estimate).mark_bar(color=TEAL, opacity=0.18, cornerRadius=4).encode(
        x=x, y=alt.Y("low:Q"), y2="high:Q",
        tooltip=[alt.Tooltip("low:Q", title="Likely low", format="$,.2f"),
                 alt.Tooltip("high:Q", title="Likely high", format="$,.2f")])
    line = alt.Chart(actual).mark_line(color=BLUE, strokeWidth=2).encode(x=x, y=_usd_axis())
    points = alt.Chart(pd.concat([actual, estimate])).mark_point(filled=True, size=80).encode(
        x=x, y="usd:Q", color=colour, tooltip=tip)
    return _style((shade + line + points).properties(height=280),
                  "Weekly spending and next-week estimate",
                  "Line = actual full weeks · teal dot = estimate · shaded = likely range · "
                  "this week is left empty until it ends")
