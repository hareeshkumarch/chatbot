import json
import re

from app.core.logging import get_logger
from app.llm.base import Message
from app.llm.prompt_registry import render_prompt_with_user_message
from app.llm.router import TaskType, router
from app.orchestration.answer_formatting import format_plan_results
from app.orchestration.graph import retrieval_graph
from app.orchestration.state import GraphContext
from app.orchestration.telemetry import record_llm_call
from app.reports.models import Report, ReportChart, ReportSection, ReportTable

logger = get_logger(__name__)

VALID_CHART_TYPES = {"bar", "line", "pie"}


def _extract_json(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()
    return json.loads(cleaned)


def _parse_report(data: dict, fallback_title: str) -> Report:
    sections = []
    for raw_section in data.get("sections", []):
        table = None
        raw_table = raw_section.get("table")
        if raw_table and raw_table.get("headers"):
            table = ReportTable(headers=[str(h) for h in raw_table.get("headers", [])], rows=[[str(c) for c in row] for row in raw_table.get("rows", [])])

        chart = None
        raw_chart = raw_section.get("chart")
        if raw_chart and raw_chart.get("labels") and raw_chart.get("chart_type") in VALID_CHART_TYPES:
            chart = ReportChart(
                title=str(raw_chart.get("title", "")),
                chart_type=raw_chart["chart_type"],
                labels=[str(label) for label in raw_chart.get("labels", [])],
                series={str(name): [float(v) for v in values] for name, values in (raw_chart.get("series") or {}).items()},
            )

        sections.append(ReportSection(
            heading=str(raw_section.get("heading", "Section")),
            paragraphs=[str(p) for p in raw_section.get("paragraphs", [])],
            table=table,
            chart=chart,
        ))

    return Report(title=str(data.get("title", fallback_title)), subtitle=str(data.get("subtitle", "")), sections=sections)


async def build_report(
    query: str,
    tenant_id: str,
    history: list[Message],
    graph_context: GraphContext,
) -> tuple[Report, list[dict], list[dict]]:
    initial_state = {
        "tenant_id": tenant_id,
        "connector_ids": [],
        "query": query,
        "history": history,
        "llm_calls": [],
    }
    state_after_retrieval = await retrieval_graph.ainvoke(initial_state, context=graph_context)
    llm_calls = state_after_retrieval.get("llm_calls", [])
    plan_results = state_after_retrieval.get("plan_results") or []

    context_text, citations, _ = format_plan_results(plan_results) if plan_results else ("", [], [])
    if not context_text.strip():
        context_text = (
            "No connected documents, databases, tools, or live data sources returned results for this topic. "
            "Write the report from general knowledge and state plainly that no supporting data was found."
        )

    messages = render_prompt_with_user_message("report_structuring", f"Context:\n{context_text}\n\nReport topic: {query}")

    try:
        response = await router.complete_with_fallback(
            TaskType.REPORT_STRUCTURING,
            messages,
            explicit_provider=graph_context.explicit_provider,
            explicit_model=graph_context.explicit_model,
            max_tokens=3000,
        )
        llm_calls = record_llm_call(
            llm_calls, "report_structuring", response.provider, response.model, response.prompt_tokens, response.completion_tokens
        )
        parsed = _extract_json(response.content)
        report = _parse_report(parsed, fallback_title=query)
    except Exception as exc:
        logger.error(f"report structuring failed, falling back to a plain summary section: {exc}")
        report = Report(title=query, subtitle="Generated report", sections=[ReportSection(heading="Summary", paragraphs=[context_text[:4000]])])

    report.citations = citations
    return report, llm_calls, plan_results
