from dataclasses import dataclass, field

from app.connectors.base import BaseConnector
from app.connectors.database.sql_connector import SQLConnector
from app.core.logging import get_logger
from app.intelligence.base import SearchResult
from app.intelligence.registry import get_answer_providers
from app.intelligence.router import (
    run_demographics_lookup,
    run_direct_answer,
    run_finance_history,
    run_finance_quote,
    run_news_search,
    run_places_search,
    run_trends_lookup,
    run_web_search,
)
from app.llm.base import Message
from app.llm.prompt_registry import render_prompt_with_user_message
from app.llm.router import TaskType, router
from app.orchestration.telemetry import record_llm_call
from app.retrieval.pipeline import run_retrieval

logger = get_logger(__name__)


@dataclass
class StepResult:
    capability: str
    parameter: str | None
    data: dict = field(default_factory=dict)
    error: str | None = None


def _search_results_to_dicts(results: list[SearchResult]) -> list[dict]:
    return [
        {"title": r.title, "url": r.url, "snippet": r.snippet, "source": r.source, "published_at": r.published_at}
        for r in results
    ]


async def execute_document_qa_step(query: str, tenant_id: str, history: list[Message]) -> StepResult:
    try:
        result = await run_retrieval(tenant_id, query, history)
        return StepResult(
            capability="document_qa",
            parameter=query,
            data={
                "chunks": [c.__dict__ for c in result.chunks],
                "confidence": result.confidence,
                "strategy": result.strategy,
            },
        )
    except Exception as exc:
        logger.error(f"document_qa step failed: {exc}")
        return StepResult(capability="document_qa", parameter=query, error=str(exc))


async def execute_sql_step(
    query: str,
    connector: SQLConnector | None,
    explicit_provider: str | None,
    explicit_model: str | None,
    llm_calls: list[dict],
) -> tuple[StepResult, list[dict]]:
    if connector is None:
        return StepResult(capability="sql_data", parameter=query, error="no SQL connector configured for this tenant"), llm_calls
    try:
        schema = await connector.get_schema()
        schema_text = "\n".join(f"{table}: {', '.join(columns)}" for table, columns in schema.items())
        messages = render_prompt_with_user_message("sql_generation", f"Schema:\n{schema_text}\n\nQuestion: {query}")
        response = await router.complete_with_fallback(
            TaskType.SQL_GENERATION, messages, explicit_provider=explicit_provider, explicit_model=explicit_model, max_tokens=300
        )
        llm_calls = record_llm_call(
            llm_calls, "sql_generation", response.provider, response.model, response.prompt_tokens, response.completion_tokens
        )
        sql = response.content.strip().strip("`")
        if sql.lower().startswith("sql"):
            sql = sql[3:].strip()
        rows = await connector.run_readonly_query(sql)
        return StepResult(capability="sql_data", parameter=query, data={"rows": rows, "sql": sql}), llm_calls
    except Exception as exc:
        logger.error(f"sql step failed: {exc}")
        return StepResult(capability="sql_data", parameter=query, error=str(exc)), llm_calls


async def execute_connector_step(query: str, active_connectors: list[BaseConnector]) -> StepResult:
    if not active_connectors:
        return StepResult(capability="connector_action", parameter=query, error="no connectors are active for this tenant")
    results: list[dict] = []
    for connector in active_connectors:
        try:
            if hasattr(connector, "search"):
                matches = await connector.search(query)
                results.extend(matches if isinstance(matches, list) else [])
            elif hasattr(connector, "search_code"):
                matches = await connector.search_code(query)
                results.extend(matches)
            elif hasattr(connector, "search_jql"):
                matches = await connector.search_jql(query)
                results.extend(matches)
        except Exception as exc:
            logger.warning(f"connector step search failed for {connector.connector_type}: {exc}")
            continue
    return StepResult(capability="connector_action", parameter=query, data={"items": results})


async def execute_web_search_step(query: str) -> StepResult:
    if get_answer_providers().get("perplexity") is not None:
        provider_name, answered = await run_direct_answer(query)
        if answered is not None:
            return StepResult(
                capability="web_search",
                parameter=query,
                data={"answer": answered.answer, "citations": answered.citations, "provider": provider_name},
            )
    provider_name, results = await run_web_search(query)
    if not results:
        return StepResult(capability="web_search", parameter=query, error="no web search results found")
    return StepResult(capability="web_search", parameter=query, data={"results": _search_results_to_dicts(results), "provider": provider_name})


async def execute_news_step(query: str) -> StepResult:
    provider_name, results = await run_news_search(query)
    if not results:
        return StepResult(capability="news", parameter=query, error="no news results found")
    return StepResult(capability="news", parameter=query, data={"results": _search_results_to_dicts(results), "provider": provider_name})


async def execute_places_step(query: str) -> StepResult:
    provider_name, results = await run_places_search(query)
    if not results:
        return StepResult(capability="places", parameter=query, error="no places provider is configured")
    return StepResult(capability="places", parameter=query, data={"results": _search_results_to_dicts(results), "provider": provider_name})


async def execute_trends_step(keyword: str) -> StepResult:
    trend = await run_trends_lookup(keyword)
    if trend is None or not trend.points:
        return StepResult(capability="trends", parameter=keyword, error="trends data is unavailable for this keyword")
    data = {
        "keyword": trend.keyword,
        "points": [{"date": p.date, "value": p.value} for p in trend.points],
        "related_queries": trend.related_queries,
    }
    return StepResult(capability="trends", parameter=keyword, data=data)


async def execute_finance_step(symbol: str) -> StepResult:
    quote = await run_finance_quote(symbol)
    if quote is None:
        return StepResult(capability="finance", parameter=symbol, error=f"could not retrieve a quote for {symbol}")
    data = {
        "symbol": quote.symbol,
        "price": quote.price,
        "currency": quote.currency,
        "change_percent": quote.change_percent,
        "market_cap": quote.market_cap,
        "pe_ratio": quote.pe_ratio,
        "fifty_two_week_high": quote.fifty_two_week_high,
        "fifty_two_week_low": quote.fifty_two_week_low,
    }
    return StepResult(capability="finance", parameter=symbol, data=data)


async def execute_demographics_step(place: str) -> StepResult:
    result = await run_demographics_lookup(place)
    if result is None:
        return StepResult(capability="demographics", parameter=place, error=f"demographics data is unavailable for {place}")
    data = {
        "place": result.place,
        "population": result.population,
        "median_household_income": result.median_household_income,
        "median_age": result.median_age,
    }
    return StepResult(capability="demographics", parameter=place, data=data)


async def execute_finance_history_step(parameter: str) -> StepResult:
    parts = parameter.split(":")
    symbol = parts[0].strip().upper() if parts else parameter.strip().upper()
    period = parts[1].strip() if len(parts) > 1 else "1y"
    valid_periods = {"1mo", "3mo", "6mo", "1y", "2y", "5y", "max"}
    if period not in valid_periods:
        period = "1y"

    try:
        points = await run_finance_history(symbol, period=period)
        if not points:
            return StepResult(capability="finance_history", parameter=symbol, error=f"no historical data found for {symbol}")
        data = {
            "symbol": symbol,
            "period": period,
            "points": [{"date": p.date, "close": p.close, "volume": p.volume} for p in points],
        }
        return StepResult(capability="finance_history", parameter=symbol, data=data)
    except Exception as exc:
        logger.error(f"finance_history step failed: {exc}")
        return StepResult(capability="finance_history", parameter=symbol, error=str(exc))
