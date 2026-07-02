from __future__ import annotations

from typing import Any


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    return str(value)


def rows_to_table(rows: list[dict], title: str, *, max_rows: int = 50) -> dict | None:
    if not rows or not isinstance(rows[0], dict):
        return None
    headers = list(rows[0].keys())
    if not headers:
        return None
    return {
        "type": "table",
        "title": title,
        "headers": headers,
        "rows": [[_cell(row.get(header)) for header in headers] for row in rows[:max_rows]],
    }


def format_rows_markdown(rows: list[dict], *, max_rows: int = 20) -> str:
    table = rows_to_table(rows, "", max_rows=max_rows)
    if not table:
        return "[]"
    headers = table["headers"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in table["rows"]:
        lines.append("| " + " | ".join(row) + " |")
    if len(rows) > max_rows:
        lines.append(f"\n(showing {max_rows} of {len(rows)} rows)")
    return "\n".join(lines)


def extract_structured_blocks(plan_results: list[dict]) -> list[dict]:
    blocks: list[dict] = []

    for result in plan_results:
        capability = result.get("capability")
        parameter = result.get("parameter")
        data = result.get("data") or {}
        if result.get("error") and not data:
            continue

        if capability == "sql_data":
            rows = data.get("rows", [])
            table = rows_to_table(rows, "Database results")
            if table:
                blocks.append(table)

        elif capability == "connector_action":
            items = data.get("items", [])
            if items and isinstance(items, list) and items and isinstance(items[0], dict):
                table = rows_to_table(items, "Connected tool results", max_rows=30)
                if table:
                    blocks.append(table)

        elif capability == "trends":
            points = data.get("points", [])
            if len(points) >= 2:
                blocks.append({
                    "type": "chart",
                    "title": f"Search interest: {data.get('keyword') or parameter or 'trend'}",
                    "chart_type": "line",
                    "labels": [str(point.get("date", idx + 1)) for idx, point in enumerate(points)],
                    "series": {
                        "Interest": [float(point.get("value", 0) or 0) for point in points],
                    },
                })

        elif capability == "finance" and data:
            symbol = str(data.get("symbol") or parameter or "Quote")
            metric_rows = [[key.replace("_", " ").title(), _cell(value)] for key, value in data.items() if key != "symbol"]
            if metric_rows:
                blocks.append({
                    "type": "table",
                    "title": f"{symbol} market data",
                    "headers": ["Metric", "Value"],
                    "rows": metric_rows,
                })

        elif capability == "demographics" and data:
            if isinstance(data, dict) and any(isinstance(v, (int, float, str)) for v in data.values()):
                blocks.append({
                    "type": "table",
                    "title": f"Demographics: {parameter or 'region'}",
                    "headers": ["Metric", "Value"],
                    "rows": [[key.replace("_", " ").title(), _cell(value)] for key, value in data.items()],
                })

    return blocks
