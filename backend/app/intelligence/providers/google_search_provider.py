import httpx

from app.core.circuit_breaker import get_circuit_breaker
from app.core.logging import get_logger
from app.intelligence.base import SearchProvider, SearchResult

logger = get_logger(__name__)


class GoogleSearchProvider(SearchProvider):
    name = "google_search"
    base_url = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: str, engine_id: str):
        self.api_key = api_key
        self.engine_id = engine_id
        self.breaker = get_circuit_breaker("intel:google_search")

    async def search(self, query: str, max_results: int = 8, location: str | None = None) -> list[SearchResult]:
        async def _do() -> list[SearchResult]:
            params = {
                "key": self.api_key,
                "cx": self.engine_id,
                "q": query,
                "num": min(max_results, 10),
            }
            if location:
                params["gl"] = location
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(self.base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return [
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=self.name,
                )
                for item in data.get("items", [])
            ]

        return await self.breaker.call(_do)
