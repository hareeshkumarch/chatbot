from app.orchestration.structured_content import extract_structured_blocks, format_rows_markdown, rows_to_table


def test_rows_to_table_from_sql_results():
    table = rows_to_table([{"region": "NA", "revenue": 100}, {"region": "EMEA", "revenue": 50}], "Results")
    assert table is not None
    assert table["headers"] == ["region", "revenue"]
    assert len(table["rows"]) == 2


def test_format_rows_markdown_renders_pipe_table():
    markdown = format_rows_markdown([{"count": 5}])
    assert "| count |" in markdown
    assert "| --- |" in markdown


def test_extract_structured_blocks_from_trends():
    blocks = extract_structured_blocks([
        {
            "capability": "trends",
            "parameter": "ai",
            "data": {"keyword": "ai", "points": [{"date": "2026-01", "value": 40}, {"date": "2026-02", "value": 55}]},
        }
    ])
    assert len(blocks) == 1
    assert blocks[0]["type"] == "chart"
    assert blocks[0]["chart_type"] == "line"
