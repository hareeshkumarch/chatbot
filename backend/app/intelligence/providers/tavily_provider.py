import httpx

from app.core.circuit_breaker import get_circuit_breaker
from app.core.logging import get_logger
from app.intelligence.base import SearchProvider, SearchResult

logger = get_logger(__name__)


class TavilyProvider(SearchProvider):
    name = "tavily"
    base_url = "https://api.tavily.com"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.breaker = get_circuit_breaker("intel:tavily")

    async def search(self, query: str, max_results: int = 8, location: str | None = None) -> list[SearchResult]:
        async def _do() -> list[SearchResult]:
            payload = {
                "query": query,
                "search_depth": "basic",
                "include_answer": False,
                "max_results": max_results,
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(f"{self.base_url}/search", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return [
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source=self.name,
                )
                for item in data.get("results", [])
            ]

        return await self.breaker.call(_do)
