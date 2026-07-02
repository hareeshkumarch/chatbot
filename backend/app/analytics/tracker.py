from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import queries_total
from app.db.models import QueryLog

COST_PER_MILLION_TOKENS: dict[str, tuple[float, float]] = {
    "anthropic": (3.0, 15.0),
    "openai": (2.5, 10.0),
    "gemini": (0.3, 2.5),
    "groq": (0.15, 0.6),
    "grok": (3.0, 15.0),
    "moonshot": (0.6, 2.5),
}


def estimate_cost_usd(provider: str, prompt_tokens: int, completion_tokens: int) -> float:
    prompt_rate, completion_rate = COST_PER_MILLION_TOKENS.get(provider, (0.0, 0.0))
    return (prompt_tokens * prompt_rate + completion_tokens * completion_rate) / 1_000_000


def summarize_llm_calls(llm_calls: list[dict]) -> tuple[int, int, float]:
    prompt_total = 0
    completion_total = 0
    cost_total = 0.0
    for call in llm_calls or []:
        prompt_tokens = max(0, int(call.get("prompt_tokens") or 0))
        completion_tokens = max(0, int(call.get("completion_tokens") or 0))
        provider = call.get("provider") or ""
        prompt_total += prompt_tokens
        completion_total += completion_tokens
        cost_total += estimate_cost_usd(provider, prompt_tokens, completion_tokens)
    return prompt_total, completion_total, round(cost_total, 6)


def token_totals(llm_calls: list[dict]) -> tuple[int, int, int]:
    prompt_tokens, completion_tokens, _ = summarize_llm_calls(llm_calls)
    return prompt_tokens, completion_tokens, prompt_tokens + completion_tokens


async def log_query(
    session: AsyncSession,
    tenant_id: str,
    conversation_id: str | None,
    query_text: str,
    plan: list[dict],
    retrieval_strategy: str,
    retrieved_chunk_count: int,
    top_relevance_score: float,
    confidence: float,
    provider: str | None,
    model: str | None,
    llm_calls: list[dict],
    latency_ms: int,
    cache_hit: bool = False,
) -> QueryLog:
    prompt_tokens, completion_tokens, cost_usd = summarize_llm_calls(llm_calls)
    entry = QueryLog(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        query_text=query_text,
        plan=plan,
        retrieval_strategy=retrieval_strategy,
        retrieved_chunk_count=retrieved_chunk_count,
        top_relevance_score=top_relevance_score,
        confidence=confidence,
        provider=provider or "none",
        model=model or "none",
        llm_calls=llm_calls,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
        cache_hit=cache_hit,
    )
    session.add(entry)
    await session.commit()
    queries_total.labels(tenant_id=tenant_id, status="success").inc()
    return entry
