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


def build_summary(score, tier, probability, flags, max_price, comfort_price, stretch_price):
    flags_lower = [f.lower() for f in flags]

    if "not affordable" in flags_lower:
        summary = (
            "This lead is not currently financeable within a practical housing range. "
            "Estimated affordability is too constrained to justify active home-search time at this stage."
        )
        action = (
            "Do not prioritize for active touring. Recommend financial preparation and lender review first."
        )
        return summary, action

    if "do not pursue due to credit score below 550" in flags_lower:
        summary = (
            "This lead is currently outside a workable credit threshold for near-term pursuit. "
            "Even if interest exists, financing execution risk is too high in its current state."
        )
        action = (
            "Do not pursue actively. Recommend credit improvement and lender consultation before re-engagement."
        )
        return summary, action

    if tier == "A" and len(flags) == 0:
        summary = (
            "This appears to be a strong lead with solid readiness and minimal visible friction. "
            "The buyer profile supports active follow-up and the estimated purchase range appears workable."
        )
        action = (
            f"High priority. Contact immediately and focus search between approximately "
            f"${round(comfort_price):,} and ${round(max_price):,}."
        )
        return summary, action

    if "dti above safe lending threshold" in flags_lower:
        summary = (
            "This lead shows meaningful affordability pressure. Debt burden appears high relative to income, "
            "which may reduce financing flexibility and increase fallout risk."
        )
        action = "Medium priority. Recommend lender review before heavy time investment."
        return summary, action

    if "dti near cap" in flags_lower:
        summary = (
            "This lead appears workable, but debt-to-income is approaching common lending thresholds. "
            "Payment expectations should be managed carefully and search discipline should remain tight."
        )
        action = (
            f"Proceed carefully. Keep search discipline near the comfort range around ${round(comfort_price):,}."
        )
        return summary, action

    if "pre-approval recommended" in flags_lower:
        summary = (
            "This buyer appears viable, but financing readiness has not yet been validated through pre-approval. "
            "That limits confidence in speed and execution."
        )
        action = "Make lender connection the first next step before committing meaningful search time."
        return summary, action

    if "representation agreement not signed" in flags_lower:
        summary = (
            "This lead may be workable, but commitment risk remains because representation has not been secured. "
            "That increases the chance of time leakage before conversion."
        )
        action = "Clarify representation expectations early before deep engagement."
        return summary, action

    summary = (
        "This lead appears moderately qualified based on the submitted information. "
        "The estimated affordability range is workable, though follow-up is needed to confirm financing readiness "
        "and strengthen execution confidence."
    )
    action = (
        f"Medium priority. Use the estimated range of ${round(comfort_price):,} to ${round(max_price):,} "
        f"as the primary planning range."
    )
    return summary, action


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
    score,
    tier,
    probability,
    max_price,
    comfort_price,
    stretch_price,
    flags,
    notes
):
    summary, action = build_summary(
        score, tier, probability, flags, max_price, comfort_price, stretch_price
    )

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    draw_header(c, buyer_name, buyer_phone, buyer_email)

    y = PAGE_HEIGHT - 125

    y = draw_section_title(c, y, "Lead Quality")
    lead_rows = [
        ("Lead Score", f"{score}"),
        ("Tier", f"{tier}"),
        ("Close Probability", f"{round(probability * 100)}%"),
    ]
    y = draw_kv_rows(c, y, lead_rows)

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

    has_no_go = any("Do not pursue due to credit score below 550" in f for f in flags)
    bullet_color = COLOR_RED if has_no_go else COLOR_TEXT
    y = draw_bullets(c, y, flags, color=bullet_color)

    if notes:
        y -= 8
        y = draw_section_title(c, y, "Notes")
        y = draw_bullets(c, y, notes, color=COLOR_SUBTLE)

    y -= 6
    y = draw_text_block(c, y, "Summary", summary, box_fill=COLOR_LIGHT)

    action_fill = HexColor("#EEF7F1") if not has_no_go else HexColor("#FDECEC")
    y = draw_text_block(c, y, "Recommended Action", action, box_fill=action_fill)

    draw_footer(c)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()