import json

import pytest

from app.reports.builder import _extract_json, _parse_report
from app.reports.charts import render_chart_png
from app.reports.docx_renderer import render_docx
from app.reports.html_renderer import render_html
from app.reports.models import Report, ReportChart, ReportSection, ReportTable, citation_label
from app.reports.pdf_renderer import render_pdf


def test_citation_label_prefers_title():
    assert citation_label({"title": "A Title", "source_uri": "https://example.com"}) == "A Title"


def test_citation_label_falls_back_to_source_uri():
    assert citation_label({"title": None, "source_uri": "https://example.com"}) == "https://example.com"


def test_citation_label_falls_back_to_source_when_both_missing():
    assert citation_label({}) == "source"


def test_extract_json_plain():
    assert _extract_json('{"title": "x"}') == {"title": "x"}


def test_extract_json_strips_markdown_fences():
    raw = '```json\n{"title": "x"}\n```'
    assert _extract_json(raw) == {"title": "x"}


def test_extract_json_strips_bare_fences():
    raw = '```\n{"title": "x"}\n```'
    assert _extract_json(raw) == {"title": "x"}


def test_extract_json_invalid_raises():
    with pytest.raises(json.JSONDecodeError):
        _extract_json("not json at all")


def test_parse_report_builds_sections_with_table_and_chart():
    data = {
        "title": "Test Report",
        "subtitle": "Sub",
        "sections": [
            {
                "heading": "Overview",
                "paragraphs": ["First para", "Second para"],
                "table": {"headers": ["A", "B"], "rows": [["1", "2"]]},
                "chart": {"title": "Chart", "chart_type": "bar", "labels": ["X", "Y"], "series": {"s1": [1, 2]}},
            }
        ],
    }
    report = _parse_report(data, fallback_title="fallback")
    assert report.title == "Test Report"
    assert len(report.sections) == 1
    assert report.sections[0].table.headers == ["A", "B"]
    assert report.sections[0].chart.chart_type == "bar"


def test_parse_report_ignores_invalid_chart_type():
    data = {"title": "x", "sections": [{"heading": "h", "paragraphs": ["p"], "chart": {"title": "c", "chart_type": "scatter", "labels": ["a"], "series": {}}}]}
    report = _parse_report(data, fallback_title="fallback")
    assert report.sections[0].chart is None


def test_parse_report_missing_table_data_is_none():
    data = {"title": "x", "sections": [{"heading": "h", "paragraphs": ["p"], "table": None}]}
    report = _parse_report(data, fallback_title="fallback")
    assert report.sections[0].table is None


def test_parse_report_uses_fallback_title_when_missing():
    data = {"sections": []}
    report = _parse_report(data, fallback_title="fallback title")
    assert report.title == "fallback title"


def _sample_report() -> Report:
    return Report(
        title="Sample <Report> & \"Test\"",
        subtitle="Subtitle",
        sections=[
            ReportSection(
                heading="Section 1",
                paragraphs=["Paragraph one.", "Paragraph two."],
                table=ReportTable(headers=["A", "B"], rows=[["1", "2"], ["3", "4"]]),
                chart=ReportChart(title="Chart", chart_type="bar", labels=["X", "Y"], series={"s": [1.0, 2.0]}),
            )
        ],
        citations=[{"index": 1, "title": "Source A", "source_uri": "https://example.com"}],
    )


def test_render_docx_produces_nonempty_valid_zip():
    output = render_docx(_sample_report())
    assert len(output) > 1000
    assert output[:2] == b"PK"


def test_render_html_escapes_injected_content():
    output = render_html(_sample_report()).decode("utf-8")
    assert "<Report>" not in output
    assert "&lt;Report&gt;" in output
    assert "Section 1" in output


def test_render_html_includes_citation_link():
    output = render_html(_sample_report()).decode("utf-8")
    assert "https://example.com" in output


def test_render_pdf_produces_valid_pdf_bytes():
    output = render_pdf(_sample_report())
    assert output[:5] == b"%PDF-"
    assert len(output) > 500


def test_render_pdf_handles_special_characters_without_crashing():
    report = Report(title="Title & <tag>", sections=[ReportSection(heading="H & <x>", paragraphs=["Text with & and < and >"])])
    output = render_pdf(report)
    assert output[:5] == b"%PDF-"


def test_render_chart_png_bar_line_pie_all_produce_bytes():
    bar = render_chart_png(ReportChart(title="t", chart_type="bar", labels=["a", "b"], series={"s": [1, 2]}))
    line = render_chart_png(ReportChart(title="t", chart_type="line", labels=["a", "b"], series={"s": [1, 2]}))
    pie = render_chart_png(ReportChart(title="t", chart_type="pie", labels=["a", "b"], series={"s": [1, 2]}))
    assert bar[:8] == b"\x89PNG\r\n\x1a\n"
    assert line[:8] == b"\x89PNG\r\n\x1a\n"
    assert pie[:8] == b"\x89PNG\r\n\x1a\n"
