import base64
import html

from app.reports.charts import render_chart_png
from app.reports.models import Report, citation_label


def _esc(text: str) -> str:
    return html.escape(text, quote=False)


def render_html(report: Report) -> bytes:
    sections_html = []
    for section in report.sections:
        paragraphs_html = "".join(f"<p>{_esc(p)}</p>" for p in section.paragraphs)

        table_html = ""
        if section.table and section.table.headers:
            header_html = "".join(f"<th>{_esc(h)}</th>" for h in section.table.headers)
            rows_html = "".join(
                "<tr>" + "".join(f"<td>{_esc(str(cell))}</td>" for cell in row) + "</tr>" for row in section.table.rows
            )
            table_html = f'<table class="report-table"><thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table>'

        chart_html = ""
        if section.chart and section.chart.labels:
            chart_bytes = render_chart_png(section.chart)
            chart_b64 = base64.b64encode(chart_bytes).decode("ascii")
            chart_html = f'<img class="report-chart" src="data:image/png;base64,{chart_b64}" alt="{_esc(section.chart.title)}" />'

        sections_html.append(
            f'<section class="report-section"><h2>{_esc(section.heading)}</h2>{paragraphs_html}{table_html}{chart_html}</section>'
        )

    citations_html = ""
    if report.citations:
        items = []
        for c in report.citations:
            label = _esc(citation_label(c))
            link = f' \u2014 <a href="{_esc(c["source_uri"])}">{_esc(c["source_uri"])}</a>' if c.get("source_uri") else ""
            items.append(f"<li>[{c.get('index')}] {label}{link}</li>")
        citations_html = f'<section class="report-section"><h2>Sources</h2><ul class="report-sources">{"".join(items)}</ul></section>'

    subtitle_html = f'<p class="subtitle">{_esc(report.subtitle)}</p>' if report.subtitle else ""

    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{_esc(report.title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600&family=Inter:wght@400;500&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --canvas: #F4F5F1; --surface: #FFFFFF; --surface-sunken: #ECEEEA;
  --ink: #14181A; --ink-muted: #5B6461; --ink-faint: #8A9390;
  --line: #DCE0DA; --route: #2F3EE0;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--canvas); color: var(--ink); font-family: 'Inter', sans-serif; line-height: 1.65; }}
.report-wrap {{ max-width: 760px; margin: 0 auto; padding: 56px 32px 96px; }}
.report-header {{ border-bottom: 1px solid var(--line); padding-bottom: 24px; margin-bottom: 32px; }}
.report-header .eyebrow {{ font-family: 'IBM Plex Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--route); margin: 0 0 8px; }}
h1 {{ font-family: 'Space Grotesk', sans-serif; font-size: 32px; margin: 0 0 8px; letter-spacing: -0.01em; }}
.subtitle {{ color: var(--ink-muted); font-size: 15px; margin: 0; }}
h2 {{ font-family: 'Space Grotesk', sans-serif; font-size: 20px; color: var(--route); margin: 40px 0 12px; }}
p {{ font-size: 15px; margin: 0 0 14px; }}
.report-table {{ width: 100%; border-collapse: collapse; margin: 16px 0 24px; font-size: 13px; }}
.report-table th {{ text-align: left; font-family: 'IBM Plex Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ink-faint); border-bottom: 1px solid var(--line); padding: 8px 12px; }}
.report-table td {{ padding: 10px 12px; border-bottom: 1px solid var(--line); }}
.report-table tr:nth-child(odd) td {{ background: var(--surface-sunken); }}
.report-chart {{ width: 100%; height: auto; border: 1px solid var(--line); border-radius: 6px; margin: 16px 0 24px; display: block; }}
.report-sources {{ list-style: none; padding: 0; font-size: 13px; color: var(--ink-muted); }}
.report-sources li {{ padding: 6px 0; border-bottom: 1px solid var(--line); }}
.report-sources a {{ color: var(--route); text-decoration: none; }}
@media print {{ body {{ background: white; }} }}
</style>
</head>
<body>
<div class="report-wrap">
  <div class="report-header">
    <p class="eyebrow">Generated report</p>
    <h1>{_esc(report.title)}</h1>
    {subtitle_html}
  </div>
  {"".join(sections_html)}
  {citations_html}
</div>
</body>
</html>"""
    return document.encode("utf-8")
