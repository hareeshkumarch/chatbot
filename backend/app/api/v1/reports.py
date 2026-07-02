import re
import time
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.tracker import log_query
from app.connectors.loader import build_active_connectors
from app.core.limits import MAX_CONNECTOR_IDS, REPORT_QUERY_MAX_LENGTH
from app.dependencies import AuthContext, get_current_user, get_db
from app.orchestration.answer_formatting import (
    extract_confidence,
    extract_document_chunk_count,
    extract_retrieval_strategy,
    extract_top_relevance_score,
)
from app.orchestration.state import GraphContext
from app.reports.builder import build_report
from app.reports.docx_renderer import render_docx
from app.reports.html_renderer import render_html
from app.reports.pdf_renderer import render_pdf

router = APIRouter(prefix="/reports", tags=["reports"])

MEDIA_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "html": "text/html",
    "pdf": "application/pdf",
}

RENDERERS = {
    "docx": render_docx,
    "html": render_html,
    "pdf": render_pdf,
}


class ReportGenerateRequest(BaseModel):
    query: str = Field(min_length=1, max_length=REPORT_QUERY_MAX_LENGTH)
    format: Literal["pdf", "docx", "html"] = "pdf"
    connector_ids: list[str] | None = Field(default=None, max_length=MAX_CONNECTOR_IDS)
    provider: str | None = None
    model: str | None = None

    @field_validator("query")
    @classmethod
    def _query_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query cannot be empty or whitespace")
        return stripped


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug[:60] or "report"


@router.post("/generate")
async def generate_report(
    payload: ReportGenerateRequest,
    auth: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Response:
    sql_connector, active_connectors = await build_active_connectors(session, auth.tenant_id, payload.connector_ids)
    graph_context = GraphContext(
        sql_connector=sql_connector,
        active_connectors=active_connectors,
        explicit_provider=payload.provider,
        explicit_model=payload.model,
    )

    start = time.monotonic()
    report, llm_calls, plan_results = await build_report(payload.query, auth.tenant_id, [], graph_context)
    latency_ms = int((time.monotonic() - start) * 1000)

    provider_used = llm_calls[-1]["provider"] if llm_calls else None
    model_used = llm_calls[-1]["model"] if llm_calls else None

    await log_query(
        session,
        tenant_id=auth.tenant_id,
        conversation_id=None,
        query_text=f"[report] {payload.query}",
        plan=[{"capability": r.get("capability"), "parameter": r.get("parameter")} for r in plan_results],
        retrieval_strategy=extract_retrieval_strategy(plan_results),
        retrieved_chunk_count=extract_document_chunk_count(plan_results),
        top_relevance_score=extract_top_relevance_score(plan_results),
        confidence=extract_confidence(plan_results) or 0.0,
        provider=provider_used,
        model=model_used,
        llm_calls=llm_calls,
        latency_ms=latency_ms,
    )

    renderer = RENDERERS[payload.format]
    file_bytes = renderer(report)
    filename = f"{_slugify(report.title)}.{payload.format}"

    return Response(
        content=file_bytes,
        media_type=MEDIA_TYPES[payload.format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
