import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.reports.charts import render_chart_png
from app.reports.models import Report, citation_label

ROUTE = colors.HexColor("#2F3EE0")
INK = colors.HexColor("#14181A")
MUTED = colors.HexColor("#5B6461")
LINE = colors.HexColor("#DCE0DA")
SUNKEN = colors.HexColor("#ECEEEA")


def _esc(text: str) -> str:
    return escape(str(text))


def render_pdf(report: Report) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=LETTER, topMargin=0.9 * inch, bottomMargin=0.9 * inch, leftMargin=0.9 * inch, rightMargin=0.9 * inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], fontSize=24, leading=28, textColor=INK, alignment=0, spaceAfter=6)
    subtitle_style = ParagraphStyle("ReportSubtitle", parent=styles["Normal"], fontSize=11, textColor=MUTED, spaceAfter=20)
    heading_style = ParagraphStyle("ReportHeading", parent=styles["Heading1"], fontSize=15, textColor=ROUTE, spaceBefore=18, spaceAfter=8)
    body_style = ParagraphStyle("ReportBody", parent=styles["Normal"], fontSize=10.5, textColor=INK, leading=16, spaceAfter=10)
    source_style = ParagraphStyle("ReportSource", parent=styles["Normal"], fontSize=9, textColor=MUTED, leading=13, spaceAfter=4)

    story = [Paragraph(_esc(report.title), title_style)]
    if report.subtitle:
        story.append(Paragraph(_esc(report.subtitle), subtitle_style))
    story.append(Spacer(1, 8))

    for section in report.sections:
        story.append(Paragraph(_esc(section.heading), heading_style))
        for paragraph_text in section.paragraphs:
            story.append(Paragraph(_esc(paragraph_text), body_style))

        if section.table and section.table.headers:
            data = [[_esc(h) for h in section.table.headers]] + [[_esc(c) for c in row] for row in section.table.rows]
            table = Table(data, hAlign="LEFT", repeatRows=1)
            table.setStyle(TableStyle([
                ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LINEBELOW", (0, 0), (-1, 0), 1, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SUNKEN]),
                ("LINEBELOW", (0, 1), (-1, -1), 0.5, LINE),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(table)
            story.append(Spacer(1, 12))

        if section.chart and section.chart.labels:
            chart_bytes = render_chart_png(section.chart, width_px=700, height_px=380)
            story.append(Image(io.BytesIO(chart_bytes), width=6 * inch, height=6 * inch * 380 / 700))
            story.append(Spacer(1, 12))

    if report.citations:
        story.append(Paragraph("Sources", heading_style))
        for citation in report.citations:
            label = citation_label(citation)
            story.append(Paragraph(f"[{citation.get('index')}] {_esc(label)} \u2014 {_esc(citation.get('source_uri', ''))}", source_style))

    doc.build(story)
    return buffer.getvalue()
