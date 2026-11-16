"""PulseIQ Task 16: monthly management PDF.
Run: python build_report.py --month 2026-09
"""
import argparse
import os
import sys
from datetime import date
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

DB_CONFIG = {
    "host": os.getenv("WAREHOUSE_HOST", "localhost"),
    "port": int(os.getenv("WAREHOUSE_PORT", "5433")),
    "dbname": os.getenv("WAREHOUSE_DB", "pulseiq_warehouse"),
    "user": os.getenv("WAREHOUSE_USER", "pulseiq"),
    "password": os.getenv("WAREHOUSE_PASSWORD", ""),
    "connect_timeout": 8,
}

MONTH_LABELS = [
    "Headcount", "Monthly Attrition", "Payroll Cost", "Overtime Share",
    "Attendance Rate", "Revenue", "Net Profit", "Operating Margin"
]

def dates_for(month_text):
    try:
        year, month = map(int, month_text.split("-"))
        if len(month_text) != 7 or not 1 <= month <= 12:
            raise ValueError
        start = date(year, month, 1)
        next_start = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        end = date.fromordinal(next_start.toordinal() - 1)
        return start, end
    except Exception:
        raise ValueError("Month must be in YYYY-MM format, for example 2026-09.")

def query_one(conn, sql, params):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()

def query_all(conn, sql, params):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()

def month_key(month_text):
    year, month = map(int, month_text.split("-"))
    return year * 12 + month

def previous_month(month_text):
    year, month = map(int, month_text.split("-"))
    if month == 1:
        return f"{year-1}-12"
    return f"{year}-{month-1:02d}"

def get_kpis(conn, month_text):
    start, end = dates_for(month_text)
    prev = previous_month(month_text)
    sqls = [
        ("SELECT COALESCE(SUM(headcount),0) FROM warehouse.metric_m01_headcount WHERE month_start_date=%s", (start,)),
        ("SELECT 100.0*SUM(exits)/NULLIF(SUM(headcount_start),0) FROM warehouse.metric_m04_monthly_attrition_rate WHERE month_start_date=%s", (start,)),
        ("SELECT SUM(payroll_cost) FROM warehouse.metric_m09_payroll_cost WHERE period_end_date=%s", (end,)),
        ("SELECT AVG(overtime_share_pct) FROM warehouse.metric_m11_overtime_share WHERE period_end_date=%s", (end,)),
        ("SELECT AVG(attendance_rate)*100 FROM warehouse.metric_m13_attendance_rate WHERE period_end_date=%s", (end,)),
        ("SELECT SUM(revenue) FROM warehouse.metric_m16_revenue WHERE posting_period=%s", (month_text,)),
        ("SELECT SUM(net_profit) FROM warehouse.metric_m17_net_profit WHERE posting_period=%s", (month_text,)),
        ("SELECT AVG(operating_margin_pct) FROM warehouse.metric_m18_operating_margin WHERE posting_period=%s", (month_text,))
    ]
    prev_start, prev_end = dates_for(prev)
    prev_params = [
        (prev_start,), (prev_start,), (prev_end,), (prev_end,),
        (prev_end,), (prev,), (prev,), (prev,)
    ]
    current, prior = [], []
    for (sql, params), pparams in zip(sqls, prev_params):
        current.append(query_one(conn, sql, params)[0])
        prior.append(query_one(conn, sql, pparams)[0])
    return current, prior

def load_financial_trend(conn, month_text, count=6):
    year, month = map(int, month_text.split("-"))
    periods = []
    for offset in range(count-1, -1, -1):
        idx = year * 12 + month - 1 - offset
        y, m0 = divmod(idx, 12)
        periods.append(f"{y}-{m0+1:02d}")
    rows = query_all(conn, """
        SELECT r.posting_period, r.revenue, p.net_profit, o.operating_margin_pct
        FROM warehouse.metric_m16_revenue r
        LEFT JOIN warehouse.metric_m17_net_profit p USING (posting_period)
        LEFT JOIN warehouse.metric_m18_operating_margin o USING (posting_period)
        WHERE r.posting_period = ANY(%s)
        ORDER BY r.posting_period
    """, (periods,))
    return rows

def load_departments(conn, month_text):
    start, end = dates_for(month_text)
    return query_all(conn, """
        SELECT d.department_name,
               h.headcount,
               p.payroll_cost,
               a.attendance_rate
        FROM warehouse.dim_department d
        LEFT JOIN warehouse.metric_m01_headcount h
          ON h.department_id=d.department_id AND h.month_start_date=%s
        LEFT JOIN warehouse.metric_m09_payroll_cost p
          ON p.department_id=d.department_id AND p.period_end_date=%s
        LEFT JOIN warehouse.metric_m13_attendance_rate a
          ON a.department_id=d.department_id AND a.period_end_date=%s
        ORDER BY d.department_name
    """, (start, end, end))

def money(value):
    if value is None:
        return "?"
    return "?{:,.2f}".format(float(value))

def number(value, decimals=2, suffix=""):
    if value is None:
        return "?"
    return f"{float(value):,.{decimals}f}{suffix}"

def delta_text(current, prior, percentage_points=False):
    if current is None or prior is None:
        return "No comparison"
    diff = float(current) - float(prior)
    if percentage_points:
        return f"{diff:+.2f} pp"
    if float(prior) == 0:
        return "?"
    return f"{(diff / abs(float(prior)) * 100):+.1f}%"

def make_bar_chart(labels, values, title, suffix="", width=450, height=190):
    drawing = Drawing(width, height)
    chart = VerticalBarChart()
    chart.x = 42
    chart.y = 34
    chart.height = height - 65
    chart.width = width - 60
    clean = [0 if v is None else float(v) for v in values]
    chart.data = [clean]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.angle = 25
    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.labelTextFormat = "%0.0f" + ("%%" if suffix == "%" else suffix)
    chart.bars[0].fillColor = colors.HexColor("#2878A8")
    chart.bars[0].strokeColor = colors.HexColor("#2878A8")
    chart.valueAxis.valueMin = min(0, min(clean, default=0))
    chart.valueAxis.valueMax = max(clean, default=1) * 1.18 or 1
    drawing.add(String(4, height-12, title, fontSize=10, fillColor=colors.HexColor("#17324D")))
    drawing.add(chart)
    return drawing

def make_line_chart(labels, values, title, width=450, height=190):
    drawing = Drawing(width, height)
    chart = HorizontalLineChart()
    chart.x = 42
    chart.y = 34
    chart.height = height - 65
    chart.width = width - 60
    clean = [0 if v is None else float(v) for v in values]
    chart.data = [clean]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.labels.fontSize = 7
    chart.lines[0].strokeColor = colors.HexColor("#2878A8")
    chart.lines[0].strokeWidth = 2
    chart.joinedLines = 1
    drawing.add(String(4, height-12, title, fontSize=10, fillColor=colors.HexColor("#17324D")))
    drawing.add(chart)
    return drawing

def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name="CoverTitle", parent=s["Title"], fontSize=24, leading=30, textColor=colors.HexColor("#17324D"), alignment=TA_CENTER, spaceAfter=12))
    s.add(ParagraphStyle(name="SubTitle", parent=s["Normal"], fontSize=10, leading=15, textColor=colors.HexColor("#526477"), alignment=TA_CENTER))
    s.add(ParagraphStyle(name="Section", parent=s["Heading2"], fontSize=14, leading=18, textColor=colors.HexColor("#17324D"), spaceBefore=12, spaceAfter=8))
    s.add(ParagraphStyle(name="SmallNote", parent=s["Normal"], fontSize=8, leading=11, textColor=colors.HexColor("#526477")))
    return s

def styled_table(data, widths=None, header=True, font_size=8):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("FONTSIZE", (0,0), (-1,-1), font_size),
        ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#D8E0E8")),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#17324D")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ]
        if len(data) > 1:
            commands.append(("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F2F6F9")]))
    t.setStyle(TableStyle(commands))
    return t

def generate(month_text, output_path):
    start, end = dates_for(month_text)
    with psycopg.connect(**DB_CONFIG) as conn:
        cutoff = query_one(conn, "SELECT CURRENT_TIMESTAMP", ())[0]
        current, prior = get_kpis(conn, month_text)
        finance = load_financial_trend(conn, month_text)
        departments = load_departments(conn, month_text)

    output = Path(output_path)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)

    s = styles()
    doc = SimpleDocTemplate(
        str(output), pagesize=A4, rightMargin=16*mm, leftMargin=16*mm,
        topMargin=17*mm, bottomMargin=17*mm, title=f"PulseIQ Monthly Report {month_text}"
    )
    story = []
    story += [
        Spacer(1, 30*mm),
        Paragraph("PULSEIQ", s["CoverTitle"]),
        Paragraph("MONTHLY WORKFORCE & FINANCIAL REPORT", s["Heading2"]),
        Spacer(1, 8*mm),
        Paragraph(f"Reporting month: <b>{month_text}</b>", s["SubTitle"]),
        Paragraph(f"Reporting date range: {start:%d %b %Y} ? {end:%d %b %Y}", s["SubTitle"]),
        Paragraph(f"Data cut-off: {cutoff:%d %b %Y, %H:%M:%S}", s["SubTitle"]),
        Spacer(1, 25*mm),
        Paragraph("Prepared from the PulseIQ warehouse reporting tables.", s["SubTitle"]),
        PageBreak()
    ]

    story.append(Paragraph("1. Executive KPI Summary", s["Section"]))
    kpi_data = [["Metric", "Current Month", "Previous Month", "Change"]]
    for label, cur, prev in zip(MONTH_LABELS, current, prior):
        if label in ("Payroll Cost", "Revenue", "Net Profit"):
            ctext, ptext = money(cur), money(prev)
        elif label == "Headcount":
            ctext, ptext = number(cur, 0), number(prev, 0)
        elif label in ("Monthly Attrition", "Overtime Share", "Attendance Rate", "Operating Margin"):
            ctext, ptext = number(cur, 2, "%"), number(prev, 2, "%")
        else:
            ctext, ptext = number(cur), number(prev)
        pp = label in ("Monthly Attrition", "Overtime Share", "Attendance Rate", "Operating Margin")
        kpi_data.append([label, ctext, ptext, delta_text(cur, prev, pp)])
    story.append(styled_table(kpi_data, [43*mm, 43*mm, 43*mm, 35*mm], font_size=7.5))
    story.append(Paragraph("Change is compared with the previous month. Percentage-point changes are shown for rate metrics.", s["SmallNote"]))

    story.append(Paragraph("2. Financial Performance ? Recent Six Months", s["Section"]))
    fin_data = [["Period", "Revenue", "Net Profit", "Operating Margin"]]
    for period, revenue, profit, margin in finance:
        fin_data.append([period, money(revenue), money(profit), number(margin, 2, "%")])
    story.append(styled_table(fin_data, [28*mm, 50*mm, 50*mm, 38*mm], font_size=7.5))
    if finance:
        labels = [r[0][2:] for r in finance]
        story.append(Spacer(1, 5*mm))
        story.append(make_bar_chart(labels, [r[1] for r in finance], "Revenue by month (?)", width=460))
        story.append(Spacer(1, 3*mm))
        story.append(make_line_chart(labels, [r[2] for r in finance], "Net profit trend (?)", width=460))

    story.append(PageBreak())
    story.append(Paragraph("3. Department Workforce Overview", s["Section"]))
    dept_data = [["Department", "Headcount", "Payroll Cost", "Attendance"]]
    missing = []
    for name, headcount, payroll, attendance in departments:
        if headcount is None and payroll is None and attendance is None:
            missing.append(name)
            continue
        dept_data.append([
            name,
            number(headcount, 0),
            money(payroll),
            number(float(attendance)*100, 2, "%") if attendance is not None else "?"
        ])
    story.append(styled_table(dept_data, [54*mm, 27*mm, 55*mm, 32*mm], font_size=7.5))
    if missing:
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("No source metric rows for: " + ", ".join(missing) + ". Missing values are not treated as zero.", s["SmallNote"]))

    story.append(Paragraph("4. Department Comparisons", s["Section"]))
    valid_payroll = [(r[0], r[2]) for r in departments if r[2] is not None]
    valid_attendance = [(r[0], float(r[3])*100) for r in departments if r[3] is not None]
    if valid_payroll:
        story.append(make_bar_chart([x[0] for x in valid_payroll], [x[1] for x in valid_payroll], "Payroll cost by department (?)", width=460, height=210))
    if valid_attendance:
        story.append(make_bar_chart([x[0] for x in valid_attendance], [x[1] for x in valid_attendance], "Attendance rate by department (%)", suffix="%", width=460, height=210))

    story.append(Paragraph("5. Data Notes & Methodology", s["Section"]))
    story.append(Paragraph(
        "The report reads the eight Task 15 warehouse KPI tables. Headcount, payroll, revenue and net profit use SUM; "
        "monthly attrition is calculated as total exits divided by total starting headcount; overtime share, attendance "
        "rate and operating margin use AVG, matching the dashboard aggregation logic. Attendance is stored as a ratio "
        "and displayed as a percentage. Department values are shown only where source records exist. The data cut-off "
        "is the warehouse database timestamp at report generation.",
        s["SmallNote"]
    ))

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#667788"))
        canvas.drawString(16*mm, 8*mm, f"PulseIQ | {month_text} | Internal report")
        canvas.drawRightString(A4[0]-16*mm, 8*mm, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output

def main():
    parser = argparse.ArgumentParser(description="Build a PulseIQ monthly management PDF.")
    parser.add_argument("--month", required=True, help="Reporting month in YYYY-MM format.")
    parser.add_argument("--output", help="PDF output path (default: reports/pulseiq_YYYY-MM.pdf).")
    args = parser.parse_args()
    try:
        dates_for(args.month)
        output = args.output or f"reports/pulseiq_{args.month}.pdf"
        path = generate(args.month, output)
        print(f"Report generated: {path}")
        print(f"Reporting month: {args.month}")
    except Exception as exc:
        print(f"Report generation failed: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
