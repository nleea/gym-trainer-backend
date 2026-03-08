"""
PDF report generation using ReportLab only.
No matplotlib, no external charting libs.
"""

from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Color palette ─────────────────────────────────────────────────────────────
PRIMARY = HexColor("#22c55e")
DARK = HexColor("#111827")
MUTED = HexColor("#6b7280")
LIGHT_BG = HexColor("#f9fafb")
WARNING = HexColor("#f59e0b")
DANGER = HexColor("#ef4444")
WHITE = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 40
CONTENT_W = PAGE_W - 2 * MARGIN

# ── Styles ────────────────────────────────────────────────────────────────────
_base = getSampleStyleSheet()


def _style(name, **kw) -> ParagraphStyle:
    s = ParagraphStyle(name, **kw)
    return s


TITLE_STYLE = _style("Title", fontSize=22, textColor=WHITE, fontName="Helvetica-Bold", spaceAfter=2)
SUB_STYLE = _style("Sub", fontSize=11, textColor=HexColor("#d1fae5"), fontName="Helvetica", spaceAfter=0)
SECTION_STYLE = _style("Section", fontSize=10, textColor=PRIMARY, fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=2)
BODY_STYLE = _style("Body", fontSize=9, textColor=DARK, fontName="Helvetica", spaceAfter=2, leading=14)
MUTED_STYLE = _style("Muted", fontSize=8, textColor=MUTED, fontName="Helvetica", spaceAfter=0)
FOOTER_STYLE = _style("Footer", fontSize=7, textColor=MUTED, fontName="Helvetica")


def _hr() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.5, color=HexColor("#e5e7eb"), spaceAfter=6, spaceBefore=6)


def _section(text: str) -> list:
    return [Paragraph(text.upper(), SECTION_STYLE), _hr()]


def _no_data() -> Paragraph:
    return Paragraph("No data recorded this month.", MUTED_STYLE)


# ── Header ────────────────────────────────────────────────────────────────────

def _build_header(data: dict) -> list:
    client = data["client"]
    period = data["period"]

    # Header table: brand left, month right
    header_table = Table(
        [[
            Paragraph("<b>MY GYM TRAINER</b>", _style("HBrand", fontSize=16, textColor=WHITE, fontName="Helvetica-Bold")),
            Paragraph(period["month"], _style("HMonth", fontSize=14, textColor=HexColor("#d1fae5"), fontName="Helvetica-Bold", alignment=2)),
        ]],
        colWidths=[CONTENT_W * 0.6, CONTENT_W * 0.4],
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (0, -1), 16),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 16),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    subtitle = Paragraph("Monthly Progress Report", _style("Subtitle", fontSize=9, textColor=MUTED, fontName="Helvetica-Bold", spaceBefore=4))

    # Client info table
    info_data = [
        ["Client:", client["name"]],
        ["Trainer:", client["trainerName"]],
        ["Period:", f"{period['startDate']} – {period['endDate']}"],
    ]
    info_table = Table(info_data, colWidths=[60, CONTENT_W - 60])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))

    return [header_table, Spacer(1, 6), subtitle, Spacer(1, 4), info_table, _hr()]


# ── Workout Summary ───────────────────────────────────────────────────────────

def _build_workout_summary(ws: dict) -> list:
    story = _section("Workout Summary")

    hours = ws["totalMinutes"] // 60
    mins = ws["totalMinutes"] % 60
    time_str = f"{hours}h {mins}m" if hours else f"{mins}m"

    stats = [
        (str(ws["totalWorkouts"]), "Workouts"),
        (f"{ws['adherencePct']}%", "Adherence"),
        (f"{ws['bestStreak']} days", "Best Streak"),
        (time_str, "Total Time"),
    ]

    cells = [[
        _stat_cell(val, label) for val, label in stats
    ]]
    t = Table(cells, colWidths=[CONTENT_W / 4] * 4)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEAFTER", (0, 0), (2, -1), 0.5, HexColor("#e5e7eb")),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    vol_kg = ws["totalVolumeKg"]
    story.append(Paragraph(
        f"Total volume lifted: <b>{vol_kg:,} kg</b>   ·   Planned workouts: <b>{ws['plannedWorkouts']}</b>",
        MUTED_STYLE,
    ))
    story.append(Spacer(1, 6))
    return story


def _stat_cell(value: str, label: str) -> Paragraph:
    return Paragraph(
        f'<b><font size="16" color="#111827">{value}</font></b><br/>'
        f'<font size="8" color="#6b7280">{label}</font>',
        _style("StatCell", alignment=1, leading=20),
    )


# ── Weekly Volume Bar Chart ───────────────────────────────────────────────────

def _build_weekly_volume_chart(weekly_volume: list) -> list:
    story = _section("Weekly Volume (kg)")

    if not weekly_volume or all(v["volume"] == 0 for v in weekly_volume):
        story.append(_no_data())
        story.append(Spacer(1, 8))
        return story

    data = [v["volume"] for v in weekly_volume]
    labels = []
    for v in weekly_volume:
        week_str = v["week"]
        # Format: "2024-03-04" → "Mar 4"
        try:
            from datetime import date as _date
            d = _date.fromisoformat(week_str)
            labels.append(d.strftime("%b %-d"))
        except Exception:
            labels.append(week_str[-5:])

    chart_width = CONTENT_W - 10
    chart_height = 90

    drawing = Drawing(chart_width, chart_height + 20)

    bc = VerticalBarChart()
    bc.x = 30
    bc.y = 15
    bc.width = chart_width - 40
    bc.height = chart_height - 10
    bc.data = [data]

    bc.bars[0].fillColor = PRIMARY
    bc.bars[0].strokeColor = None

    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(data) * 1.2 if max(data) > 0 else 1000
    bc.valueAxis.valueStep = max(data) * 0.2 if max(data) > 0 else 200
    bc.valueAxis.labelTextFormat = lambda v: f"{int(v):,}"
    bc.valueAxis.labels.fontSize = 7
    bc.valueAxis.labels.fillColor = MUTED

    bc.categoryAxis.categoryNames = labels
    bc.categoryAxis.labels.fontSize = 7
    bc.categoryAxis.labels.fillColor = MUTED
    bc.categoryAxis.labels.angle = 0

    drawing.add(bc)
    story.append(drawing)
    story.append(Spacer(1, 8))
    return story


# ── PRs Section ───────────────────────────────────────────────────────────────

def _build_prs_section(prs: list) -> list:
    story = _section("Personal Records")

    if not prs:
        story.append(_no_data())
        story.append(Spacer(1, 8))
        return story

    rows = [["Exercise", "Previous", "New", "Gain"]]
    for pr in prs[:8]:
        gain = pr["newWeight"] - pr["previousBest"]
        rows.append([
            pr["exerciseName"],
            f"{pr['previousBest']} kg",
            f"{pr['newWeight']} kg",
            Paragraph(f'<font color="#22c55e"><b>+{gain} kg</b></font>', BODY_STYLE),
        ])

    t = Table(rows, colWidths=[CONTENT_W * 0.45, CONTENT_W * 0.18, CONTENT_W * 0.18, CONTENT_W * 0.19])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 8))
    return story


# ── Body Metrics ──────────────────────────────────────────────────────────────

def _build_body_metrics(body_metrics: dict) -> list:
    story = _section("Body Metrics")

    metric_map = [
        ("Weight", "weight", "kg"),
        ("Body Fat %", "bodyFatPct", "%"),
        ("Waist", "waistCm", "cm"),
    ]

    rows = [["Metric", "Start", "End", "Change"]]
    any_data = False
    for label, key, unit in metric_map:
        m = body_metrics.get(key)
        if not m:
            rows.append([label, "—", "—", "—"])
            continue
        any_data = True
        change = m["change"]
        # For weight and body fat, negative is good (green); for waist too
        color = "#22c55e" if change <= 0 else "#ef4444"
        sign = "+" if change > 0 else ""
        change_cell = Paragraph(
            f'<font color="{color}"><b>{sign}{change}{unit}</b></font>',
            BODY_STYLE,
        )
        rows.append([
            label,
            f"{m['start']}{unit}",
            f"{m['end']}{unit}",
            change_cell,
        ])

    if not any_data:
        story.append(_no_data())
        story.append(Spacer(1, 8))
        return story

    t = Table(rows, colWidths=[CONTENT_W * 0.35, CONTENT_W * 0.2, CONTENT_W * 0.2, CONTENT_W * 0.25])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 8))
    return story


# ── Exercise Progress ─────────────────────────────────────────────────────────

def _build_exercise_progress(exercise_progress: list) -> list:
    story = _section("Exercise Progress (Top 5)")

    if not exercise_progress:
        story.append(_no_data())
        story.append(Spacer(1, 8))
        return story

    rows = [["Exercise", "Start", "End", "Change", "Sessions"]]
    for ep in exercise_progress[:5]:
        change = ep["change"]
        sign = "+" if change > 0 else ""
        color = "#22c55e" if change > 0 else ("#6b7280" if change == 0 else "#ef4444")
        arrow = "▲" if change > 0 else ("▼" if change < 0 else "—")
        change_cell = Paragraph(
            f'<font color="{color}"><b>{sign}{change} kg {arrow}</b></font>',
            BODY_STYLE,
        )
        rows.append([
            ep["exerciseName"],
            f"{ep['startWeight']} kg",
            f"{ep['endWeight']} kg",
            change_cell,
            str(ep["totalSessions"]),
        ])

    t = Table(rows, colWidths=[
        CONTENT_W * 0.35, CONTENT_W * 0.16, CONTENT_W * 0.16, CONTENT_W * 0.22, CONTENT_W * 0.11
    ])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 8))
    return story


# ── Nutrition Adherence ───────────────────────────────────────────────────────

def _build_nutrition_adherence(nutrition: dict) -> list:
    story = _section("Nutrition")

    days_logged = nutrition["daysLogged"]
    total_days = nutrition["totalDays"]
    pct = nutrition["adherencePct"]
    avg_cal = nutrition["avgCalories"]
    avg_prot = nutrition["avgProtein"]

    if days_logged == 0:
        story.append(_no_data())
        story.append(Spacer(1, 8))
        return story

    color = "#22c55e" if pct >= 70 else ("#f59e0b" if pct >= 40 else "#ef4444")
    story.append(Paragraph(
        f'Days logged: <b>{days_logged}/{total_days}</b> '
        f'(<font color="{color}"><b>{pct}%</b></font>)',
        BODY_STYLE,
    ))
    story.append(Paragraph(
        f"Avg calories: <b>{avg_cal:,} kcal</b>   ·   Avg protein: <b>{avg_prot}g</b>",
        BODY_STYLE,
    ))
    story.append(Spacer(1, 8))
    return story


# ── Checkins Summary ──────────────────────────────────────────────────────────

def _build_checkins_summary(checkins: list) -> list:
    story = _section("Weekly Wellbeing")

    if not checkins:
        story.append(_no_data())
        story.append(Spacer(1, 8))
        return story

    rows = [["Week", "Sleep", "Energy", "Stress", "Mood"]]
    for c in checkins:
        week_str = c.get("weekStart", "")
        try:
            from datetime import date as _date
            d = _date.fromisoformat(week_str)
            week_label = d.strftime("%b %-d")
        except Exception:
            week_label = week_str

        sleep = f"{c['sleepHours']}h" if c.get("sleepHours") is not None else "—"
        energy = f"{c['energyLevel']}/10" if c.get("energyLevel") is not None else "—"
        stress = f"{c['stressLevel']}/10" if c.get("stressLevel") is not None else "—"
        mood = (c.get("mood") or "—").replace("_", " ").title()
        rows.append([week_label, sleep, energy, stress, mood])

    t = Table(rows, colWidths=[
        CONTENT_W * 0.2, CONTENT_W * 0.15, CONTENT_W * 0.2, CONTENT_W * 0.2, CONTENT_W * 0.25
    ])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 8))
    return story


# ── Footer ────────────────────────────────────────────────────────────────────

def _build_footer(data: dict) -> list:
    generated_str = datetime.now().strftime("%B %-d, %Y")
    return [
        _hr(),
        Paragraph(
            f"Generated {generated_str}   ·   My Gym Trainer",
            FOOTER_STYLE,
        ),
    ]


# ── Table style helper ────────────────────────────────────────────────────────

def _table_style() -> TableStyle:
    return TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f3f4f6")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
        # Body rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), DARK),
        # Alternating rows
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.3, HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_monthly_report(data: dict) -> BytesIO:
    """Generate the PDF report and return an in-memory buffer."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )

    story = []
    story += _build_header(data)
    story += _build_workout_summary(data["workoutSummary"])
    story += _build_weekly_volume_chart(data["weeklyVolume"])
    story += _build_prs_section(data["prs"])
    story += _build_body_metrics(data["bodyMetrics"])
    story += _build_exercise_progress(data["exerciseProgress"])
    story += _build_nutrition_adherence(data["nutritionAdherence"])
    story += _build_checkins_summary(data["checkins"])
    story += _build_footer(data)

    doc.build(story)
    buffer.seek(0)
    return buffer
