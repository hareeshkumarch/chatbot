from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import QueryLog
from app.analytics.tracker import estimate_cost_usd


def _aggregate_call_usage(rows: list[tuple[list | None, list | None]]) -> tuple[
    dict[str, dict[str, int]],
    dict[tuple[str, str], dict[str, int]],
    dict[str, dict[str, int]],
]:
    by_provider: dict[str, dict[str, int | float]] = defaultdict(lambda: {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0})
    by_model: dict[tuple[str, str], dict[str, int | float]] = defaultdict(lambda: {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0})
    by_task: dict[str, dict[str, int]] = defaultdict(lambda: {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0})

    for plan, calls in rows:
        for step in plan or []:
            _ = step
        for call in calls or []:
            provider = call.get("provider") or "unknown"
            model = call.get("model") or "unknown"
            task = call.get("task") or "unknown"
            prompt_tokens = max(0, int(call.get("prompt_tokens") or 0))
            completion_tokens = max(0, int(call.get("completion_tokens") or 0))

            call_cost = estimate_cost_usd(provider, prompt_tokens, completion_tokens)

            provider_stats = by_provider[provider]
            provider_stats["calls"] += 1
            provider_stats["prompt_tokens"] += prompt_tokens
            provider_stats["completion_tokens"] += completion_tokens
            provider_stats["cost_usd"] = float(provider_stats["cost_usd"]) + call_cost

            model_stats = by_model[(provider, model)]
            model_stats["calls"] += 1
            model_stats["prompt_tokens"] += prompt_tokens
            model_stats["completion_tokens"] += completion_tokens
            model_stats["cost_usd"] = float(model_stats["cost_usd"]) + call_cost

            task_stats = by_task[task]
            task_stats["calls"] += 1
            task_stats["prompt_tokens"] += prompt_tokens
            task_stats["completion_tokens"] += completion_tokens

    return by_provider, by_model, by_task


async def get_dashboard_metrics(session: AsyncSession, tenant_id: str, days: int = 7) -> dict:
    since = datetime.utcnow() - timedelta(days=days)
    filters = (QueryLog.tenant_id == tenant_id, QueryLog.created_at >= since)

    summary = (await session.execute(
        select(
            func.count(QueryLog.id),
            func.coalesce(func.sum(QueryLog.prompt_tokens), 0),
            func.coalesce(func.sum(QueryLog.completion_tokens), 0),
            func.coalesce(func.sum(QueryLog.cost_usd), 0.0),
            func.coalesce(func.avg(QueryLog.latency_ms), 0.0),
            func.coalesce(func.avg(QueryLog.confidence), 0.0),
            func.count(case((QueryLog.cache_hit.is_(True), 1))),
        ).where(*filters)
    )).one()

    total_queries, prompt_tokens, completion_tokens, cost_usd, avg_latency, avg_confidence, cache_hits = summary
    prompt_tokens = int(prompt_tokens)
    completion_tokens = int(completion_tokens)
    total_tokens = prompt_tokens + completion_tokens

    by_provider_rows = (await session.execute(
        select(QueryLog.provider, func.count(QueryLog.id), func.coalesce(func.sum(QueryLog.cost_usd), 0.0))
        .where(*filters)
        .group_by(QueryLog.provider)
    )).all()

    day_bucket = func.date_trunc("day", QueryLog.created_at).label("day_bucket")

    by_day_rows = (await session.execute(
        select(
            day_bucket,
            func.count(QueryLog.id),
            func.coalesce(func.sum(QueryLog.prompt_tokens), 0),
            func.coalesce(func.sum(QueryLog.completion_tokens), 0),
            func.coalesce(func.sum(QueryLog.cost_usd), 0.0),
            func.coalesce(func.avg(QueryLog.confidence), 0.0),
        )
        .where(*filters)
        .group_by(day_bucket)
        .order_by(day_bucket)
    )).all()

    by_strategy_rows = (await session.execute(
        select(QueryLog.retrieval_strategy, func.count(QueryLog.id))
        .where(*filters)
        .group_by(QueryLog.retrieval_strategy)
    )).all()

    json_rows = (await session.execute(select(QueryLog.plan, QueryLog.llm_calls).where(*filters))).all()
    capability_counts: dict[str, int] = defaultdict(int)
    for plan, _calls in json_rows:
        for step in plan or []:
            capability_counts[step.get("capability", "unknown")] += 1

    call_by_provider, call_by_model, task_breakdown = _aggregate_call_usage(json_rows)

    return {
        "total_queries": total_queries,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "avg_tokens_per_query": round(total_tokens / total_queries, 1) if total_queries else 0.0,
        "total_cost_usd": round(float(cost_usd), 4),
        "avg_latency_ms": round(float(avg_latency), 1),
        "avg_confidence": round(float(avg_confidence), 3),
        "cache_hit_rate": round(cache_hits / total_queries, 3) if total_queries else 0.0,
        "by_provider": [
            {
                "provider": provider,
                "queries": next((queries for p, queries, _cost in by_provider_rows if p == provider), 0),
                "llm_calls": int(stats["calls"]),
                "prompt_tokens": int(stats["prompt_tokens"]),
                "completion_tokens": int(stats["completion_tokens"]),
                "total_tokens": int(stats["prompt_tokens"]) + int(stats["completion_tokens"]),
                "cost_usd": round(float(stats["cost_usd"]), 4),
            }
            for provider, stats in sorted(
                call_by_provider.items(),
                key=lambda item: -(int(item[1]["prompt_tokens"]) + int(item[1]["completion_tokens"])),
            )
        ],
        "by_model": [
            {
                "provider": provider,
                "model": model,
                "queries": int(stats["calls"]),
                "prompt_tokens": int(stats["prompt_tokens"]),
                "completion_tokens": int(stats["completion_tokens"]),
                "total_tokens": int(stats["prompt_tokens"]) + int(stats["completion_tokens"]),
                "cost_usd": round(float(stats["cost_usd"]), 4),
            }
            for (provider, model), stats in sorted(
                call_by_model.items(),
                key=lambda item: -(int(item[1]["prompt_tokens"]) + int(item[1]["completion_tokens"])),
            )
        ],
        "by_day": [
            {
                "date": day.date().isoformat(),
                "queries": query_count,
                "prompt_tokens": int(prompt),
                "completion_tokens": int(completion),
                "tokens": int(prompt) + int(completion),
                "cost_usd": round(float(cost), 4),
                "avg_confidence": round(float(conf), 3),
            }
            for day, query_count, prompt, completion, cost, conf in by_day_rows
        ],
        "by_retrieval_strategy": [{"strategy": strategy, "queries": count} for strategy, count in by_strategy_rows],
        "by_capability": [{"capability": key, "count": value} for key, value in sorted(capability_counts.items(), key=lambda kv: -kv[1])],
        "by_task": [
            {
                "task": task,
                "calls": int(stats["calls"]),
                "prompt_tokens": int(stats["prompt_tokens"]),
                "completion_tokens": int(stats["completion_tokens"]),
                "total_tokens": int(stats["prompt_tokens"] + stats["completion_tokens"]),
            }
            for task, stats in sorted(task_breakdown.items(), key=lambda kv: -(kv[1]["prompt_tokens"] + kv[1]["completion_tokens"]))
        ],
    }


async def get_query_trace(session: AsyncSession, tenant_id: str, query_log_id: str) -> QueryLog | None:
    result = await session.execute(select(QueryLog).where(QueryLog.id == query_log_id, QueryLog.tenant_id == tenant_id))
    return result.scalar_one_or_none()


async def list_recent_traces(session: AsyncSession, tenant_id: str, limit: int = 50) -> list[QueryLog]:
    result = await session.execute(
        select(QueryLog).where(QueryLog.tenant_id == tenant_id).order_by(QueryLog.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())
