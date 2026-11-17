"""Create a polished SmartCash product design PDF for review and handoff."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import legal, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas


OUT = Path("output/pdf/smartcash-ui-design.pdf")
W, H = landscape(legal)

NAVY = colors.HexColor("#FFFFFF")
BLUE = colors.HexColor("#2563EB")
CYAN = colors.HexColor("#0EA5A4")
INK = colors.HexColor("#172B4D")
MUTED = colors.HexColor("#64748B")
BG = colors.HexColor("#FFFFFF")
CARD = colors.white
LINE = colors.HexColor("#E5E7EB")
GREEN = colors.HexColor("#16803C")
AMBER = colors.HexColor("#B45309")
RED = colors.HexColor("#C2413B")
PURPLE = colors.HexColor("#7C3AED")

styles = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9, leading=12, textColor=INK)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=7.5, leading=10, textColor=MUTED)
WHITE = ParagraphStyle("white", parent=BODY, textColor=colors.white)


def text(c, value, x, y, size=9, color=INK, font="Helvetica"):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, value)


def paragraph(c, value, x, y, width, height, style=BODY):
    p = Paragraph(value, style)
    _, used_height = p.wrap(width, height)
    p.drawOn(c, x, y + height - used_height)


def rounded(c, x, y, w, h, fill=CARD, stroke=LINE, radius=10):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def pill(c, label, x, y, fill=BLUE, width=None):
    width = width or stringWidth(label, "Helvetica-Bold", 7) + 18
    c.setFillColor(fill)
    c.roundRect(x, y, width, 17, 8, fill=1, stroke=0)
    text(c, label, x + 9, y + 5, 7, colors.white, "Helvetica-Bold")
    return width


def header(c, title, subtitle, page_no):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.rect(0, H - 58, W, 58, fill=1, stroke=0)
    c.setStrokeColor(LINE)
    c.line(0, H - 58, W, H - 58)
    c.setFillColor(CYAN)
    c.circle(31, H - 29, 12, fill=1, stroke=0)
    text(c, "$", 26, H - 34, 13, colors.white, "Helvetica-Bold")
    text(c, "SMARTCASH", 51, H - 25, 12, INK, "Helvetica-Bold")
    text(c, "Personal finance, made clear", 51, H - 40, 8, MUTED)
    text(c, title, 260, H - 27, 15, INK, "Helvetica-Bold")
    text(c, subtitle, 260, H - 42, 8, MUTED)
    text(c, f"{_CURRENT_PAGE or page_no:02d}", W - 46, H - 33, 9, MUTED, "Helvetica-Bold")


def sidebar(c, active):
    x, y, w, h = 24, 34, 145, H - 108
    rounded(c, x, y, w, h, fill=colors.HexColor("#F8FAFC"), stroke=LINE, radius=12)
    text(c, "Workspace", x + 17, y + h - 29, 8, MUTED, "Helvetica-Bold")
    items = ["Overview", "Transactions", "Budgets", "Forecast", "Study insights"]
    for i, item in enumerate(items):
        iy = y + h - 66 - i * 34
        if item == active:
            c.setFillColor(colors.HexColor("#EAF0F8"))
            c.roundRect(x + 8, iy - 8, w - 16, 26, 8, fill=1, stroke=0)
        c.setFillColor(CYAN if item == active else colors.HexColor("#94A3B8"))
        c.circle(x + 24, iy + 5, 4, fill=1, stroke=0)
        text(c, item, x + 38, iy + 1, 8, INK if item == active else MUTED, "Helvetica-Bold" if item == active else "Helvetica")
    c.setStrokeColor(LINE)
    c.line(x + 15, y + 85, x + w - 15, y + 85)
    text(c, "Privacy first", x + 17, y + 62, 8, CYAN, "Helvetica-Bold")
    paragraph(c, "No names or account numbers. Insights use anonymous aggregates.", x + 17, y + 20, w - 34, 38, ParagraphStyle("side", parent=SMALL, textColor=MUTED))


def card(c, x, y, w, h, label, value, delta=None, accent=BLUE):
    rounded(c, x, y, w, h)
    c.setFillColor(accent)
    c.roundRect(x, y + h - 5, w, 5, 3, fill=1, stroke=0)
    text(c, label, x + 14, y + h - 25, 8, MUTED, "Helvetica-Bold")
    text(c, value, x + 14, y + 23, 20, INK, "Helvetica-Bold")
    if delta:
        text(c, delta, x + w - stringWidth(delta, "Helvetica-Bold", 8) - 14, y + 25, 8, GREEN if "up" in delta.lower() else AMBER, "Helvetica-Bold")


def line_chart(c, x, y, w, h):
    rounded(c, x, y, w, h)
    text(c, "Weekly spending", x + 16, y + h - 25, 11, INK, "Helvetica-Bold")
    text(c, "USD totals with a 4-week average", x + 16, y + h - 40, 8, MUTED)
    left, bottom = x + 38, y + 33
    cw, ch = w - 56, h - 85
    c.setStrokeColor(LINE)
    for i in range(4):
        gy = bottom + i * ch / 3
        c.line(left, gy, left + cw, gy)
        text(c, f"${i * 20}", x + 8, gy - 3, 7, MUTED)
    vals = [34, 43, 39, 51, 47, 58, 53, 61, 55, 66]
    pts = []
    c.setStrokeColor(BLUE)
    c.setLineWidth(2.5)
    for i, val in enumerate(vals):
        px = left + i * cw / (len(vals) - 1)
        py = bottom + val / 70 * ch
        pts.append((px, py))
        if i:
            c.line(pts[i - 1][0], pts[i - 1][1], px, py)
    c.setFillColor(BLUE)
    for px, py in pts:
        c.circle(px, py, 2.8, fill=1, stroke=0)
    c.setStrokeColor(CYAN)
    c.setLineWidth(1.5)
    for i in range(1, len(pts)):
        c.line(pts[i - 1][0], (pts[i - 1][1] + pts[i][1]) / 2, pts[i][0], (pts[i - 1][1] + pts[i][1]) / 2)
    for i, label in enumerate(["W1", "W3", "W5", "W7", "W9"]):
        text(c, label, left + i * cw / 4 - 5, y + 17, 7, MUTED)
    pill(c, "Actual", x + w - 115, y + h - 33, BLUE, 46)
    pill(c, "4-week avg", x + w - 64, y + h - 33, CYAN, 52)


def bars(c, x, y, w, h):
    rounded(c, x, y, w, h)
    text(c, "Top categories", x + 16, y + h - 25, 11, INK, "Helvetica-Bold")
    text(c, "This month - biggest first", x + 16, y + h - 40, 8, MUTED)
    vals = [("Food & drinks", 96, BLUE), ("Transport", 72, CYAN), ("Shopping", 58, PURPLE), ("Entertainment", 41, AMBER), ("Education", 28, GREEN)]
    maxv = 100
    for i, (label, val, color) in enumerate(vals):
        yy = y + h - 67 - i * 28
        text(c, label, x + 16, yy + 3, 8, INK)
        c.setFillColor(colors.HexColor("#E8EEF5"))
        c.roundRect(x + 104, yy, w - 145, 12, 6, fill=1, stroke=0)
        c.setFillColor(color)
        c.roundRect(x + 104, yy, (w - 145) * val / maxv, 12, 6, fill=1, stroke=0)
        text(c, f"${val}", x + w - 32, yy + 2, 8, INK, "Helvetica-Bold")


_CURRENT_PAGE = 0


def footer(c, page_no=None):
    c.setStrokeColor(LINE)
    c.line(24, 22, W - 24, 22)
    text(c, "SmartCash UI design concept | USD and KHR | 2026", 24, 10, 7, MUTED)
    text(c, f"Page {_CURRENT_PAGE or page_no}", W - 72, 10, 7, MUTED)


def page_overview(c):
    header(c, "Overview", "Answer the user's question before showing the detail", 1)
    sidebar(c, "Overview")
    x = 190
    text(c, "Good morning, Darren", x, 465, 21, INK, "Helvetica-Bold")
    text(c, "Here is your money picture for this month.", x, 447, 9, MUTED)
    pill(c, "This month", W - 135, 445, colors.HexColor("#E7EEF8"), 88)
    c.setFillColor(INK)
    c.roundRect(W - 125, 445, 8, 17, 4, fill=1, stroke=0)
    card(c, x, 355, 150, 70, "Income", "$260.00", "up 4%", GREEN)
    card(c, x + 162, 355, 150, 70, "Spending", "$251.30", "up 9%", AMBER)
    card(c, x + 324, 355, 150, 70, "Net cash flow", "+ $8.70", "down $12", BLUE)
    card(c, x + 486, 355, 150, 70, "Savings rate", "3.3%", "down 4.6 pts", PURPLE)
    line_chart(c, x, 117, 360, 213)
    bars(c, x + 380, 117, 256, 213)
    footer(c, 1)


def page_transactions(c):
    header(c, "Transactions", "Capture every purchase without making it feel like accounting", 2)
    sidebar(c, "Transactions")
    x = 190
    text(c, "Transactions", x, 465, 21, INK, "Helvetica-Bold")
    text(c, "Review, filter, and add income or expenses.", x, 447, 9, MUTED)
    pill(c, "+ Add transaction", W - 160, 443, BLUE, 112)
    rounded(c, x, 399, 640, 32, fill=colors.white)
    text(c, "Dates: This month", x + 14, 410, 8, INK, "Helvetica-Bold")
    text(c, "Category: All", x + 170, 410, 8, MUTED)
    text(c, "Type: All", x + 310, 410, 8, MUTED)
    pill(c, "Export CSV", x + 540, 407, colors.HexColor("#E7EEF8"), 76)
    rounded(c, x, 112, 640, 266)
    headers = ["DATE", "TYPE", "CATEGORY", "PAYMENT", "AMOUNT", "USD"]
    positions = [x + 16, x + 112, x + 190, x + 337, x + 465, x + 558]
    for label, px in zip(headers, positions):
        text(c, label, px, 350, 7, MUTED, "Helvetica-Bold")
    rows = [
        ("Nov 09", "Expense", "Food & drinks", "Cash", "3.50 USD", "$3.50"),
        ("Nov 08", "Expense", "Transport", "QR", "8,000 KHR", "$1.95"),
        ("Nov 07", "Income", "Allowance", "Bank", "100.00 USD", "$100.00"),
        ("Nov 06", "Expense", "Education", "Card", "8.00 USD", "$8.00"),
        ("Nov 05", "Expense", "Groceries", "Cash", "12,000 KHR", "$2.93"),
    ]
    for i, row in enumerate(rows):
        yy = 319 - i * 39
        c.setStrokeColor(LINE)
        c.line(x + 14, yy - 10, x + 626, yy - 10)
        for value, px in zip(row, positions):
            text(c, value, px, yy, 8, INK if value != "Income" else GREEN, "Helvetica-Bold" if value in ("Income", "$100.00") else "Helvetica")
    footer(c, 2)


def page_budgets(c):
    header(c, "Budgets", "Turn a number into a next action", 3)
    sidebar(c, "Budgets")
    x = 190
    text(c, "Monthly budgets", x, 465, 21, INK, "Helvetica-Bold")
    text(c, "Set limits by category and see what is left.", x, 447, 9, MUTED)
    pill(c, "+ Add budget", W - 145, 443, BLUE, 98)
    items = [("Food & drinks", 96, 120, RED, "Over by $6"), ("Transport", 28, 45, GREEN, "$17 left"), ("Shopping & care", 24, 30, AMBER, "$6 left"), ("Entertainment", 41, 35, RED, "Over by $6")]
    for i, (label, used, limit, color, status) in enumerate(items):
        yy = 350 - i * 70
        rounded(c, x, yy, 640, 52)
        text(c, label, x + 16, yy + 31, 9, INK, "Helvetica-Bold")
        text(c, f"${used} of ${limit}", x + 16, yy + 14, 8, MUTED)
        c.setFillColor(colors.HexColor("#E8EEF5"))
        c.roundRect(x + 165, yy + 20, 270, 12, 6, fill=1, stroke=0)
        c.setFillColor(color)
        c.roundRect(x + 165, yy + 20, min(270, 270 * used / limit), 12, 6, fill=1, stroke=0)
        pill(c, status, x + 490, yy + 18, color if color != RED else RED, 105)
    rounded(c, x, 92, 640, 48, fill=colors.HexColor("#EAF7F5"), stroke=colors.HexColor("#B7E4DE"))
    text(c, "Tip", x + 16, 119, 8, CYAN, "Helvetica-Bold")
    text(c, "You have $17 left in Transport. Keep this pace and you will stay on track.", x + 48, 119, 9, INK)
    footer(c, 3)


def page_forecast(c):
    header(c, "Forecast", "Be honest about uncertainty", 4)
    sidebar(c, "Forecast")
    x = 190
    text(c, "Next week forecast", x, 465, 21, INK, "Helvetica-Bold")
    text(c, "An estimate based on recent spending - not a promise.", x, 447, 9, MUTED)
    card(c, x, 351, 190, 70, "Likely spending", "$53", "estimate", BLUE)
    card(c, x + 204, 351, 190, 70, "Likely range", "$45 - $61", "premium", PURPLE)
    card(c, x + 408, 351, 190, 70, "Past accuracy", "82%", "last 4 weeks", GREEN)
    rounded(c, x, 120, 598, 200)
    text(c, "Weekly spending and forecast", x + 16, 290, 11, INK, "Helvetica-Bold")
    text(c, "Solid = actual | dashed = estimate | shaded = likely range", x + 16, 275, 8, MUTED)
    left, bottom, cw, ch = x + 44, 151, 515, 94
    c.setStrokeColor(LINE)
    for i in range(4):
        gy = bottom + i * ch / 3
        c.line(left, gy, left + cw, gy)
    actual = [38, 46, 42, 51, 49, 58, 53]
    pts = []
    c.setStrokeColor(BLUE); c.setLineWidth(2.5)
    for i, val in enumerate(actual):
        px = left + i * cw / 7
        py = bottom + val / 70 * ch
        if i: c.line(pts[-1][0], pts[-1][1], px, py)
        pts.append((px, py))
    c.setStrokeColor(PURPLE); c.setDash(5, 4); c.line(pts[-1][0], pts[-1][1], left + cw, bottom + 53 / 70 * ch); c.setDash()
    c.setFillColor(colors.HexColor("#EDE9FE")); c.setFillAlpha(0.7)
    c.rect(left + cw * 7 / 8, bottom + 45 / 70 * ch, cw / 8, 20 / 70 * ch, fill=1, stroke=0); c.setFillAlpha(1)
    for label, px in [("W1", left), ("W4", left + cw * 3 / 8), ("W7", left + cw * 6 / 8), ("Next", left + cw)]:
        text(c, label, px - 8, 134, 7, MUTED)
    footer(c, 4)


def page_insights(c):
    header(c, "Study insights", "Show the group story without exposing any person", 5)
    sidebar(c, "Study insights")
    x = 190
    text(c, "What the group data shows", x, 465, 21, INK, "Helvetica-Bold")
    text(c, "Anonymous and aggregated only - minimum group size: 5.", x, 447, 9, MUTED)
    card(c, x, 355, 180, 70, "Participants", "25", "consented", BLUE)
    card(c, x + 194, 355, 180, 70, "Transactions", "1,248", "5 weeks", CYAN)
    card(c, x + 388, 355, 210, 70, "Median weekly spend", "$42", "USD equivalent", PURPLE)
    rounded(c, x, 120, 290, 205)
    text(c, "Cash vs digital", x + 16, 292, 11, INK, "Helvetica-Bold")
    c.setFillColor(BLUE); c.circle(x + 101, 218, 62, fill=1, stroke=0)
    c.setFillColor(CYAN); c.wedge(x + 39, 156, x + 163, 280, 0, 122, fill=1, stroke=0)
    text(c, "Cash 52%", x + 192, 239, 9, INK, "Helvetica-Bold")
    text(c, "QR / mobile 41%", x + 192, 217, 9, INK, "Helvetica-Bold")
    text(c, "Card / other 7%", x + 192, 195, 9, INK, "Helvetica-Bold")
    rounded(c, x + 310, 120, 288, 205)
    text(c, "Food share by living situation", x + 326, 292, 11, INK, "Helvetica-Bold")
    groups = [("Dorm", 44), ("Renting", 58), ("With family", 37)]
    for i, (label, val) in enumerate(groups):
        yy = 237 - i * 44
        text(c, label, x + 326, yy + 2, 8, INK)
        c.setFillColor(colors.HexColor("#E8EEF5")); c.roundRect(x + 400, yy, 120, 12, 6, fill=1, stroke=0)
        c.setFillColor(CYAN); c.roundRect(x + 400, yy, val * 2, 12, 6, fill=1, stroke=0)
        text(c, f"{val}%", x + 535, yy + 2, 8, INK, "Helvetica-Bold")
    footer(c, 5)


def page_add(c):
    header(c, "Add transaction", "A calm, fast entry flow for a real-life Tuesday", 6)
    sidebar(c, "Transactions")
    x = 228
    rounded(c, x, 88, 520, 350)
    text(c, "Add transaction", x + 26, 405, 17, INK, "Helvetica-Bold")
    text(c, "Record it now. Understand it later.", x + 26, 387, 8, MUTED)
    text(c, "Type", x + 26, 350, 8, MUTED, "Helvetica-Bold")
    pill(c, "Expense", x + 26, 320, BLUE, 70)
    pill(c, "Income", x + 105, 320, colors.HexColor("#E7EEF8"), 67)
    text(c, "Amount", x + 26, 290, 8, MUTED, "Helvetica-Bold")
    rounded(c, x + 26, 252, 210, 31, fill=colors.HexColor("#F8FAFC"))
    text(c, "3.50", x + 40, 263, 12, INK, "Helvetica-Bold")
    pill(c, "USD", x + 249, 259, CYAN, 54)
    text(c, "Date", x + 26, 220, 8, MUTED, "Helvetica-Bold")
    rounded(c, x + 26, 182, 210, 31, fill=colors.HexColor("#F8FAFC"))
    text(c, "09 Nov 2026", x + 40, 193, 10, INK)
    text(c, "Category", x + 249, 220, 8, MUTED, "Helvetica-Bold")
    rounded(c, x + 249, 182, 214, 31, fill=colors.HexColor("#F8FAFC"))
    text(c, "Food & drinks    v", x + 263, 193, 9, INK)
    text(c, "Paid with", x + 26, 150, 8, MUTED, "Helvetica-Bold")
    text(c, "Note (optional)", x + 249, 150, 8, MUTED, "Helvetica-Bold")
    rounded(c, x + 26, 112, 210, 27, fill=colors.HexColor("#F8FAFC"))
    text(c, "Cash", x + 40, 122, 9, INK)
    rounded(c, x + 249, 112, 214, 27, fill=colors.HexColor("#F8FAFC"))
    text(c, "Lunch near campus", x + 263, 122, 9, MUTED)
    pill(c, "Save transaction", x + 350, 62, BLUE, 112)
    footer(c, 6)


def page_system(c):
    header(c, "Design system", "Simple rules keep every screen readable and trustworthy", 7)
    sidebar(c, "Overview")
    x = 190
    text(c, "Visual language", x, 465, 21, INK, "Helvetica-Bold")
    text(c, "Use the same meaning, spacing, and color behavior everywhere.", x, 447, 9, MUTED)
    rounded(c, x, 245, 250, 160)
    text(c, "Colors", x + 18, 378, 11, INK, "Helvetica-Bold")
    swatches = [("Navy", NAVY), ("Blue", BLUE), ("Teal", CYAN), ("Green", GREEN), ("Amber", AMBER), ("Red", RED)]
    for i, (label, color) in enumerate(swatches):
        sx = x + 18 + (i % 3) * 73; sy = 335 - (i // 3) * 50
        c.setFillColor(color); c.circle(sx + 10, sy + 8, 10, fill=1, stroke=0)
        text(c, label, sx + 26, sy + 5, 8, INK)
    rounded(c, x + 270, 245, 328, 160)
    text(c, "Writing and chart rules", x + 288, 378, 11, INK, "Helvetica-Bold")
    rules = ["Lead with the answer, then explain why.", "Use USD on converted charts and label currency.", "Never use color alone to show meaning.", "Bars compare; lines show change; progress shows budget."]
    for i, rule in enumerate(rules):
        c.setFillColor(CYAN); c.circle(x + 294, 350 - i * 27, 3, fill=1, stroke=0)
        text(c, rule, x + 305, 347 - i * 27, 8, INK)
    rounded(c, x, 98, 598, 115, fill=colors.HexColor("#EAF7F5"), stroke=colors.HexColor("#B7E4DE"))
    text(c, "Product promise", x + 18, 185, 11, CYAN, "Helvetica-Bold")
    paragraph(c, "SmartCash helps students see where their money goes, understand what is changing, and prepare for next week - without pretending that an estimate is certain.", x + 18, 120, 550, 55, ParagraphStyle("quote", parent=BODY, fontSize=13, leading=18, textColor=INK))
    footer(c, 7)


SCREENSHOTS = [
    (Path(r"C:\Users\User\AppData\Roaming\Code\agentSessionData\12362d1f-e5e3-4f53-bd18-092d3d2d0bde\attachments\ea4aa824-4e78-4e13-bba0-e9540744f0bb\Pasted Image.png"), "Add transaction", "Current working Streamlit screen"),
    (Path(r"C:\Users\User\AppData\Roaming\Code\agentSessionData\12362d1f-e5e3-4f53-bd18-092d3d2d0bde\attachments\c8b5f75e-70a3-4c07-a640-b3812ee22d36\Pasted Image 2.png"), "Import diary", "CSV upload and participant ID flow"),
    (Path(r"C:\Users\User\AppData\Roaming\Code\agentSessionData\12362d1f-e5e3-4f53-bd18-092d3d2d0bde\attachments\276662f3-5a6c-4b00-b886-2bf5549e184e\Pasted Image 3.png"), "Transactions", "Filterable transaction list"),
    (Path(r"C:\Users\User\AppData\Roaming\Code\agentSessionData\12362d1f-e5e3-4f53-bd18-092d3d2d0bde\attachments\c0dcde8e-bae5-46d1-87e4-7681fc3e3e2c\Pasted Image 4.png"), "Dashboard", "Current empty-state dashboard"),
]


def page_gallery(c):
    header(c, "Current app screens", "The working Streamlit screens are the starting point for the visual direction", 1)
    text(c, "SmartCash today", 36, H - 88, 18, INK, "Helvetica-Bold")
    text(c, "These screens are the real application surface. The following pages refine the same structure into a polished product design.", 36, H - 105, 8, MUTED)
    positions = [(36, 232), (510, 232), (36, 52), (510, 52)]
    tile_w, tile_h = 438, 155
    for (image_path, title, _), (x, y) in zip(SCREENSHOTS, positions):
        rounded(c, x, y, tile_w, tile_h, fill=colors.white, stroke=LINE, radius=8)
        text(c, title, x + 12, y + tile_h - 20, 9, INK, "Helvetica-Bold")
        if image_path.exists():
            image = ImageReader(str(image_path))
            iw, ih = image.getSize()
            max_w, max_h = tile_w - 24, tile_h - 35
            scale = min(max_w / iw, max_h / ih)
            draw_w, draw_h = iw * scale, ih * scale
            c.drawImage(image, x + (tile_w - draw_w) / 2, y + 8, width=draw_w, height=draw_h, preserveAspectRatio=True, mask="auto")
    footer(c, 1)


def page_screenshot(c, image_path, title, subtitle, page_no):
    header(c, title, subtitle, page_no)
    text(c, "Screen design", 36, H - 88, 16, INK, "Helvetica-Bold")
    text(c, "Current SmartCash Streamlit screen used as the design source.", 36, H - 103, 8, MUTED)
    if not image_path.exists():
        rounded(c, 36, 60, W - 72, H - 190, fill=colors.HexColor("#F8FAFC"))
        text(c, "Screenshot not found", 60, H / 2, 12, RED, "Helvetica-Bold")
    else:
        image = ImageReader(str(image_path))
        iw, ih = image.getSize()
        max_w, max_h = W - 120, H - 155
        scale = min(max_w / iw, max_h / ih)
        draw_w, draw_h = iw * scale, ih * scale
        draw_x = (W - draw_w) / 2
        draw_y = 38 + (H - 125 - draw_h) / 2
        c.setFillColor(colors.white)
        c.setStrokeColor(LINE)
        c.roundRect(draw_x - 8, draw_y - 8, draw_w + 16, draw_h + 16, 8, fill=1, stroke=1)
        c.drawImage(image, draw_x, draw_y, width=draw_w, height=draw_h, preserveAspectRatio=True, mask="auto")
    footer(c, page_no)


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H))
    global _CURRENT_PAGE
    for _CURRENT_PAGE, page in enumerate(
        [page_overview, page_transactions, page_budgets, page_forecast,
         page_insights, page_add, page_system], start=1
    ):
        page(c)
        c.showPage()
    c.save()
    print(OUT.resolve())


if __name__ == "__main__":
    build()
