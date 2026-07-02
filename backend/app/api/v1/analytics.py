from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.aggregator import get_dashboard_metrics, get_query_trace, list_recent_traces
from app.core.phoenix_tracing import phoenix_trace_url
from app.dependencies import AuthContext, get_current_user, get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


class ProviderBreakdown(BaseModel):
    provider: str
    queries: int
    llm_calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class DayBreakdown(BaseModel):
    date: str
    queries: int
    prompt_tokens: int
    completion_tokens: int
    tokens: int
    cost_usd: float
    avg_confidence: float


class StrategyBreakdown(BaseModel):
    strategy: str
    queries: int


class CapabilityBreakdown(BaseModel):
    capability: str
    count: int


class TaskBreakdown(BaseModel):
    task: str
    calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ModelBreakdown(BaseModel):
    provider: str
    model: str
    queries: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class DashboardMetricsOut(BaseModel):
    total_queries: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    avg_tokens_per_query: float
    total_cost_usd: float
    avg_latency_ms: float
    avg_confidence: float
    cache_hit_rate: float
    by_provider: list[ProviderBreakdown]
    by_model: list[ModelBreakdown]
    by_day: list[DayBreakdown]
    by_retrieval_strategy: list[StrategyBreakdown]
    by_capability: list[CapabilityBreakdown]
    by_task: list[TaskBreakdown]


class TraceLlmCall(BaseModel):
    task: str
    provider: str | None
    model: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class TraceOut(BaseModel):
    id: str
    query_text: str
    plan: list[dict]
    retrieval_strategy: str
    confidence: float
    provider: str
    model: str
    llm_calls: list[TraceLlmCall]
    llm_call_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int
    created_at: str
    phoenix_trace_url: str | None = None


def _to_trace_out(row) -> TraceOut:
    return TraceOut(
        id=row.id,
        query_text=row.query_text,
        plan=row.plan,
        retrieval_strategy=row.retrieval_strategy,
        confidence=row.confidence,
        provider=row.provider,
        model=row.model,
        llm_calls=[TraceLlmCall(**{**call, "total_tokens": int(call.get("prompt_tokens", 0)) + int(call.get("completion_tokens", 0))}) for call in row.llm_calls],
        llm_call_count=len(row.llm_calls or []),
        prompt_tokens=row.prompt_tokens,
        completion_tokens=row.completion_tokens,
        total_tokens=row.prompt_tokens + row.completion_tokens,
        cost_usd=row.cost_usd,
        latency_ms=row.latency_ms,
        created_at=row.created_at.isoformat(),
        phoenix_trace_url=phoenix_trace_url(row.conversation_id) if row.conversation_id else None,
    )


@router.get("/dashboard", response_model=DashboardMetricsOut)
async def dashboard(
    days: int = Query(default=7, ge=1, le=90),
    auth: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DashboardMetricsOut:
    data = await get_dashboard_metrics(session, auth.tenant_id, days)
    return DashboardMetricsOut(**data)


@router.get("/traces", response_model=list[TraceOut])
async def recent_traces(
    limit: int = Query(default=50, ge=1, le=200),
    auth: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[TraceOut]:
    rows = await list_recent_traces(session, auth.tenant_id, limit)
    return [_to_trace_out(r) for r in rows]


@router.get("/traces/{query_log_id}", response_model=TraceOut)
async def get_trace(
    query_log_id: str, auth: AuthContext = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> TraceOut:
    row = await get_query_trace(session, auth.tenant_id, query_log_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="trace not found")
    return _to_trace_out(row)
