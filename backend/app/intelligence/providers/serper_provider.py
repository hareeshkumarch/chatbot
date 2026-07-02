import httpx

from app.core.circuit_breaker import get_circuit_breaker
from app.core.logging import get_logger
from app.intelligence.base import SearchProvider, SearchResult

logger = get_logger(__name__)


class SerperProvider(SearchProvider):
    name = "serper"
    base_url = "https://google.serper.dev"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.breaker = get_circuit_breaker("intel:serper")

    def _headers(self) -> dict:
        return {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

    async def search(self, query: str, max_results: int = 8, location: str | None = None) -> list[SearchResult]:
        async def _do() -> list[SearchResult]:
            payload = {"q": query, "num": max_results}
            if location:
                payload["location"] = location
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{self.base_url}/search", headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            return [
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=self.name,
                    published_at=item.get("date"),
                )
                for item in data.get("organic", [])[:max_results]
            ]

        return await self.breaker.call(_do)

    async def search_news(self, query: str, max_results: int = 8, location: str | None = None) -> list[SearchResult]:
        async def _do() -> list[SearchResult]:
            payload = {"q": query, "num": max_results}
            if location:
                payload["location"] = location
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{self.base_url}/news", headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            return [
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=item.get("source", self.name),
                    published_at=item.get("date"),
                )
                for item in data.get("news", [])[:max_results]
            ]

        return await self.breaker.call(_do)

    async def search_places(self, query: str, max_results: int = 8, location: str | None = None) -> list[SearchResult]:
        async def _do() -> list[SearchResult]:
            payload = {"q": query, "num": max_results}
            if location:
                payload["location"] = location
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{self.base_url}/places", headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("places", [])[:max_results]:
                address = item.get("address", "")
                rating = item.get("rating")
                snippet = f"{address}" + (f" · rated {rating}" if rating else "")
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("website") or item.get("cid", ""),
                        snippet=snippet,
                        source=self.name,
                    )
                )
            return results

        return await self.breaker.call(_do)
