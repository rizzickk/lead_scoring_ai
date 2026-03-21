from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas


# -----------------------------
# STYLE
# -----------------------------
PAGE_WIDTH, PAGE_HEIGHT = letter

MARGIN_X = 50
CONTENT_WIDTH = PAGE_WIDTH - (MARGIN_X * 2)

COLOR_NAVY = HexColor("#16324F")
COLOR_GOLD = HexColor("#D9A441")
COLOR_LIGHT = HexColor("#F4F6F8")
COLOR_MID = HexColor("#D9DEE3")
COLOR_TEXT = HexColor("#1F2933")
COLOR_SUBTLE = HexColor("#52606D")
COLOR_RED = HexColor("#B42318")
COLOR_GREEN = HexColor("#1B7A3E")


# -----------------------------
# HELPERS
# -----------------------------
def split_text(text, max_chars=92):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        if len(test) <= max_chars:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def draw_header(c, buyer_name, buyer_phone, buyer_email):
    c.setFillColor(COLOR_NAVY)
    c.rect(0, PAGE_HEIGHT - 95, PAGE_WIDTH, 95, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(MARGIN_X, PAGE_HEIGHT - 38, "Lead Scoring AI")

    c.setFont("Helvetica", 10)
    c.drawString(MARGIN_X, PAGE_HEIGHT - 55, "Agent Lead Intelligence Report")

    c.setFillColor(COLOR_GOLD)
    c.rect(MARGIN_X, PAGE_HEIGHT - 72, 140, 3, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 38, "Buyer Contact")

    c.setFont("Helvetica", 10)
    c.drawRightString(PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 54, buyer_name)
    c.drawRightString(PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 68, buyer_phone)
    c.drawRightString(PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 82, buyer_email)


def draw_section_title(c, y, title):
    c.setStrokeColor(COLOR_MID)
    c.setLineWidth(1)
    c.line(MARGIN_X, y + 8, PAGE_WIDTH - MARGIN_X, y + 8)

    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(MARGIN_X, y - 4, title)
    return y - 22


def draw_kv_rows(c, y, rows, value_x=240, row_gap=18):
    c.setFont("Helvetica", 10.5)
    for label, value in rows:
        c.setFillColor(COLOR_SUBTLE)
        c.drawString(MARGIN_X, y, label)

        c.setFillColor(COLOR_TEXT)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(value_x, y, value)

        c.setFont("Helvetica", 10.5)
        y -= row_gap
    return y


def draw_bullets(c, y, items, color=COLOR_TEXT, row_gap=17):
    c.setFont("Helvetica", 10.5)
    c.setFillColor(color)

    if not items:
        c.drawString(MARGIN_X + 12, y, "No major risks detected")
        return y - row_gap

    for item in items:
        c.circle(MARGIN_X + 4, y + 3, 1.6, fill=1, stroke=0)
        c.drawString(MARGIN_X + 12, y, item)
        y -= row_gap
    return y


def draw_text_block(c, y, title, text, box_fill=COLOR_LIGHT):
    lines = split_text(text, 92)

    box_top = y
    box_height = 22 + (len(lines) * 15) + 14

    c.setFillColor(box_fill)
    c.setStrokeColor(COLOR_MID)
    c.roundRect(MARGIN_X, box_top - box_height, CONTENT_WIDTH, box_height, 10, fill=1, stroke=1)

    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN_X + 14, box_top - 18, title)

    c.setFillColor(COLOR_TEXT)
    c.setFont("Helvetica", 10.5)

    line_y = box_top - 36
    for line in lines:
        c.drawString(MARGIN_X + 14, line_y, line)
        line_y -= 15

    return box_top - box_height - 18


def draw_footer(c):
    c.setStrokeColor(COLOR_MID)
    c.line(MARGIN_X, 42, PAGE_WIDTH - MARGIN_X, 42)

    c.setFont("Helvetica-Oblique", 8.5)
    c.setFillColor(COLOR_SUBTLE)
    c.drawString(
        MARGIN_X,
        28,
        "Internal agent-use report. Not a loan approval or lending decision."
    )


# -----------------------------
# MAIN PDF
# -----------------------------
def generate_report_bytes(
    buyer_name,
    buyer_phone,
    buyer_email,
    disposition,
    priority_score,
    tier,
    max_price,
    comfort_price,
    stretch_price,
    flags,
    notes,
    recommended_next_step,
):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    draw_header(c, buyer_name, buyer_phone, buyer_email)

    y = PAGE_HEIGHT - 125

    y = draw_section_title(c, y, "Lead Assessment")

    is_no_pursue = disposition == "Do Not Pursue"
    disposition_color = COLOR_RED if is_no_pursue else (COLOR_GREEN if disposition == "Active Opportunity" else COLOR_GOLD)

    c.setFont("Helvetica", 10.5)
    c.setFillColor(COLOR_SUBTLE)
    c.drawString(MARGIN_X, y, "Disposition")
    c.setFont("Helvetica-Bold", 10.5)
    c.setFillColor(disposition_color)
    c.drawString(240, y, disposition)
    y -= 18

    assessment_rows = [
        ("Priority Score", f"{priority_score}"),
        ("Tier", f"{tier}"),
    ]
    y = draw_kv_rows(c, y, assessment_rows)

    y -= 8
    y = draw_section_title(c, y, "Affordability Snapshot")
    affordability_rows = [
        ("Comfort Price", f"${round(comfort_price):,}"),
        ("Max Home Price", f"${round(max_price):,}"),
        ("Stretch Price", f"${round(stretch_price):,}"),
    ]
    y = draw_kv_rows(c, y, affordability_rows)

    y -= 8
    y = draw_section_title(c, y, "Flags")
    bullet_color = COLOR_RED if is_no_pursue else COLOR_TEXT
    y = draw_bullets(c, y, flags, color=bullet_color)

    if notes:
        y -= 8
        y = draw_section_title(c, y, "Notes")
        y = draw_bullets(c, y, notes, color=COLOR_SUBTLE)

    y -= 6
    action_fill = HexColor("#FDECEC") if is_no_pursue else (HexColor("#EEF7F1") if disposition == "Active Opportunity" else COLOR_LIGHT)
    y = draw_text_block(c, y, "Recommended Next Step", recommended_next_step, box_fill=action_fill)

    draw_footer(c)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()
