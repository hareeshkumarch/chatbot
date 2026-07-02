from app.core.logging import get_logger
from app.intelligence.base import AnsweredResult, DemographicsResult, FinanceQuote, SearchResult, TrendsResult
from app.intelligence.registry import (
    get_answer_providers,
    get_demographics_providers,
    get_duckduckgo_provider,
    get_finance_provider,
    get_google_news_rss_provider,
    get_search_providers,
    get_serper_provider,
    get_trends_provider,
)

logger = get_logger(__name__)

WEB_SEARCH_ROUTING: list[str] = ["tavily", "exa", "serper", "google_search"]
NEWS_FALLBACK_ROUTING: list[str] = ["tavily", "exa", "google_search"]


async def run_web_search(query: str, location: str | None = None, max_results: int = 8) -> tuple[str, list[SearchResult]]:
    providers = get_search_providers()
    chain = [name for name in WEB_SEARCH_ROUTING if name in providers]
    last_error: Exception | None = None
    for name in chain:
        try:
            results = await providers[name].search(query, max_results=max_results, location=location)
            if results:
                return name, results
        except Exception as exc:
            logger.warning(f"web search provider {name} failed: {exc}")
            last_error = exc
            continue

    try:
        ddg = get_duckduckgo_provider()
        results = await ddg.search(query, max_results=max_results, location=location)
        if results:
            return "duckduckgo", results
    except Exception as exc:
        logger.warning(f"duckduckgo web search fallback failed: {exc}")
        last_error = exc

    if last_error is not None:
        raise last_error
    return "", []


async def run_news_search(query: str, location: str | None = None, max_results: int = 8) -> tuple[str, list[SearchResult]]:
    serper = get_serper_provider()
    if serper is not None:
        try:
            results = await serper.search_news(query, max_results=max_results, location=location)
            if results:
                return "serper", results
        except Exception as exc:
            logger.warning(f"serper news search failed: {exc}")

    providers = get_search_providers()
    for name in NEWS_FALLBACK_ROUTING:
        if name not in providers:
            continue
        try:
            results = await providers[name].search(f"{query} latest news", max_results=max_results, location=location)
            if results:
                return name, results
        except Exception as exc:
            logger.warning(f"news fallback provider {name} failed: {exc}")
            continue

    try:
        rss = get_google_news_rss_provider()
        results = await rss.search_news(query, max_results=max_results, location=location)
        if results:
            return "google_news_rss", results
    except Exception as exc:
        logger.warning(f"google news rss fallback failed: {exc}")

    try:
        ddg = get_duckduckgo_provider()
        results = await ddg.search_news(query, max_results=max_results, location=location)
        if results:
            return "duckduckgo", results
    except Exception as exc:
        logger.warning(f"duckduckgo news fallback failed: {exc}")

    return "", []


async def run_places_search(query: str, location: str | None = None, max_results: int = 8) -> tuple[str, list[SearchResult]]:
    serper = get_serper_provider()
    if serper is None:
        return "", []
    try:
        results = await serper.search_places(query, max_results=max_results, location=location)
        return "serper", results
    except Exception as exc:
        logger.warning(f"serper places search failed: {exc}")
        return "", []


async def run_direct_answer(query: str) -> tuple[str, AnsweredResult | None]:
    perplexity = get_answer_providers().get("perplexity")
    if perplexity is None:
        return "", None
    try:
        result = await perplexity.answer(query)
        return "perplexity", result
    except Exception as exc:
        logger.warning(f"perplexity direct answer failed: {exc}")
        return "", None


async def run_trends_lookup(keyword: str, geo: str = "") -> TrendsResult | None:
    try:
        return await get_trends_provider().interest_over_time(keyword, geo=geo)
    except Exception as exc:
        logger.warning(f"google trends lookup failed for {keyword}: {exc}")
        return None


async def run_finance_quote(symbol: str) -> FinanceQuote | None:
    try:
        return await get_finance_provider().quote(symbol)
    except Exception as exc:
        logger.warning(f"yahoo finance quote failed for {symbol}: {exc}")
        return None


async def run_finance_history(symbol: str, period: str = "1mo") -> list:
    try:
        return await get_finance_provider().history(symbol, period=period)
    except Exception as exc:
        logger.warning(f"yahoo finance history failed for {symbol}: {exc}")
        return []


async def run_demographics_lookup(place: str) -> DemographicsResult | None:
    census = get_demographics_providers().get("census")
    if census is None:
        return None
    try:
        return await census.lookup(place)
    except Exception as exc:
        logger.warning(f"census demographics lookup failed for {place}: {exc}")
        return None


def available_intelligence_capabilities() -> dict[str, list[str]]:
    serper_available = get_serper_provider() is not None
    web_providers = list(get_search_providers().keys()) + ["duckduckgo"]
    news_providers = ["google_news_rss", "duckduckgo"]
    if serper_available:
        news_providers.insert(0, "serper")
    return {
        "web_search": web_providers,
        "direct_answer": list(get_answer_providers().keys()),
        "news": news_providers,
        "places": ["serper"] if serper_available else [],
        "trends": ["google_trends"],
        "finance": ["yahoo_finance"],
        "finance_history": ["yahoo_finance"],
        "demographics": list(get_demographics_providers().keys()),
    }
