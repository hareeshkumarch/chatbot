import asyncio

from app.core.circuit_breaker import get_circuit_breaker
from app.core.logging import get_logger
from app.intelligence.base import SearchProvider, SearchResult

logger = get_logger(__name__)


class DuckDuckGoProvider(SearchProvider):
    name = "duckduckgo"

    def __init__(self) -> None:
        self.breaker = get_circuit_breaker("intel:duckduckgo")

    async def search(self, query: str, max_results: int = 8, location: str | None = None) -> list[SearchResult]:
        async def _do() -> list[SearchResult]:
            loop = asyncio.get_event_loop()

            def _sync() -> list[SearchResult]:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    raw = list(ddgs.text(query, max_results=max_results, region=location or "wt-wt"))
                return [
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("href", ""),
                        snippet=r.get("body", ""),
                        source="duckduckgo",
                    )
                    for r in raw
                ]

            return await loop.run_in_executor(None, _sync)

        return await self.breaker.call(_do)

    async def search_news(self, query: str, max_results: int = 8, location: str | None = None) -> list[SearchResult]:
        async def _do() -> list[SearchResult]:
            loop = asyncio.get_event_loop()

            def _sync() -> list[SearchResult]:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    raw = list(ddgs.news(query, max_results=max_results, region=location or "wt-wt"))
                return [
                    SearchResult(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        snippet=r.get("body", ""),
                        source=r.get("source", "duckduckgo"),
                        published_at=r.get("date"),
                    )
                    for r in raw
                ]

            return await loop.run_in_executor(None, _sync)

        return await self.breaker.call(_do)
