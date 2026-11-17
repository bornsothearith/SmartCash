"""Build the customer-facing SmartCash Sprint 2 progress report."""

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "SmartCash_Sprint_2_Customer_Report_Final.docx"

NAVY = "172B4D"
BLUE = "2563EB"
TEAL = "0EA5A4"
MUTED = "64748B"
LIGHT = "F8FAFC"
BORDER = "D9E2EC"
GREEN = "166534"
AMBER = "92400E"


def set_cell_shading(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_border(cell, color=BORDER, size="6"):
    properties = cell._tc.get_or_add_tcPr()
    borders = properties.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        properties.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:color"), color)


def set_cell_text(cell, value, bold=False, color=NAVY, size=9):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.space_before = Pt(0)
    run = paragraph.add_run(value)
    run.bold = bold
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        set_cell_shading(cell, NAVY)
        set_cell_text(cell, header, bold=True, color="FFFFFF", size=8.5)
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cell = cells[index]
            set_cell_shading(cell, "FFFFFF" if row_index % 2 == 0 else LIGHT)
            set_cell_text(cell, value, size=8.5)
    for row in table.rows:
        for index, cell in enumerate(row.cells):
            set_cell_border(cell)
            if widths:
                cell.width = Inches(widths[index])
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_bullet(doc, text):
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(3)
    run = paragraph.add_run(text)
    run.font.name = "Aptos"
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor.from_string(NAVY)
    return paragraph


def add_heading(doc, text, level=1):
    paragraph = doc.add_heading(text, level=level)
    paragraph.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(5)
    return paragraph


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor.from_string(NAVY)
    normal.paragraph_format.space_after = Pt(6)

    for style_name, size, color in (("Title", 26, NAVY), ("Heading 1", 16, NAVY), ("Heading 2", 12, BLUE)):
        style = doc.styles[style_name]
        style.font.name = "Aptos Display" if style_name == "Title" else "Aptos"
        style._element.rPr.rFonts.set(qn("w:ascii"), style.font.name)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), style.font.name)
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run("SmartCash | Sprint 2 Customer Progress Report")
    footer_run.font.name = "Aptos"
    footer_run.font.size = Pt(8)
    footer_run.font.color.rgb = RGBColor.from_string(MUTED)

    title = doc.add_paragraph(style="Title")
    title.add_run("SmartCash Sprint 2 Customer Progress Report")
    title.paragraph_format.space_after = Pt(4)
    subtitle = doc.add_paragraph("Sprint period 3 November to 9 November | Prepared for customer review")
    subtitle.paragraph_format.space_after = Pt(16)
    subtitle.runs[0].font.color.rgb = RGBColor.from_string(MUTED)
    subtitle.runs[0].font.size = Pt(11)

    intro = doc.add_paragraph()
    intro.add_run("Purpose. ").bold = True
    intro.add_run(
        "This report explains what the SmartCash team completed during Sprint 2. "
        "The sprint focused on preparing the application to collect spending-diary data, "
        "protect participant privacy, handle USD and KHR amounts, and present spending clearly."
    )

    add_heading(doc, "Sprint outcome", 1)
    doc.add_paragraph(
        "The core Sprint 2 application workflow is working. A user can record an income or expense, "
        "import a diary CSV, filter transactions, view USD-equivalent summaries, review weekly spending "
        "charts, and set category budgets. Privacy documentation and daily exchange-rate handling were also added."
    )

    add_heading(doc, "Work completed", 1)
    rows = [
        ("SCG-25", "Spending diary form", "Completed", "Added transaction entry, income and expense types, USD and KHR selection, categories, payment method, notes, and CSV diary import."),
        ("SCG-28", "USD/KHR exchange-rate table", "Completed", "Added daily exchange-rate storage and conversion of KHR transactions to USD using the transaction date."),
        ("SCG-68", "Keep real data private", "Completed", "Added privacy rules, anonymous participant IDs, consent guidance, and a privacy notice in the application."),
        ("SCG-20", "Figma UI design and user flow", "Completed", "Implemented the white and light-gray interface direction, navigation, dashboard cards, budget view, and chart layout."),
        ("SCG-21", "Architecture and database diagrams", "Completed", "Added the system-flow diagram and database ER diagram to docs/architecture.md."),
        ("SCG-26", "Recruit volunteers and launch diary", "Ready to launch", "Prepared the invitation, Google Form structure, CSV hand-off rules, and launch checklist. The team must publish the form and recruit volunteers."),
        ("SCG-155", "Sprint review deck and submission", "Ready to submit", "Prepared the customer report and final review checklist. The team must attach external evidence and submit through the course channel."),
    ]
    add_table(doc, ["Ticket", "Work item", "Status", "Customer-visible result"], rows, [0.55, 1.45, 1.05, 3.95])

    add_heading(doc, "Customer visible features", 1)
    add_bullet(doc, "Add transaction: record income or expenses in USD or KHR with date, category, payment method, and an optional note.")
    add_bullet(doc, "Import diary: upload a CSV spending diary and receive duplicate and rejected-row feedback.")
    add_bullet(doc, "Dashboard: see income, spending, net cash flow, savings rate, weekly spending, moving average, and category breakdown.")
    add_bullet(doc, "Budgets: set monthly category limits and see spending progress, remaining amounts, and budget status.")
    add_bullet(doc, "Privacy: the application warns users not to enter names, account numbers, passwords, or other unnecessary personal information.")

    add_heading(doc, "Quality evidence", 1)
    add_table(
        doc,
        ["Check", "Result"],
        [
            ("Automated Sprint 1 and Sprint 2 tests", "14 tests passed"),
            ("Python compilation check", "Passed for the main app, budget page, and theme"),
            ("Application diagnostics", "No errors found in checked files"),
        ],
        [3.1, 3.9],
    )

    add_heading(doc, "Items requiring external team action", 1)
    add_bullet(doc, "Publish the approved Google Form and recruit volunteers using docs/volunteer-recruitment.md.")
    add_bullet(doc, "Attach the Google Form link, consent evidence, diary import screenshot, duplicate/rejected-row screenshot, and dashboard screenshot.")
    add_bullet(doc, "Submit this report and the Sprint 2 review checklist through the agreed course or project channel.")

    add_heading(doc, "Next sprint recommendation", 1)
    doc.add_paragraph(
        "The next priority should be completing the volunteer data-collection workflow and connecting approved diary responses to the application. "
        "After that, the team can improve forecast and study-insight pages using privacy-safe aggregated data."
    )

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
