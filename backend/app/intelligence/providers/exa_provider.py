import httpx

from app.core.circuit_breaker import get_circuit_breaker
from app.core.logging import get_logger
from app.intelligence.base import SearchProvider, SearchResult

logger = get_logger(__name__)


class ExaProvider(SearchProvider):
    name = "exa"
    base_url = "https://api.exa.ai"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.breaker = get_circuit_breaker("intel:exa")

    async def search(self, query: str, max_results: int = 8, location: str | None = None) -> list[SearchResult]:
        async def _do() -> list[SearchResult]:
            payload = {
                "query": query,
                "numResults": max_results,
                "contents": {"highlights": True},
            }
            headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(f"{self.base_url}/search", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("results", []):
                highlights = item.get("highlights") or []
                snippet = " ".join(highlights) if highlights else (item.get("summary") or "")
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=snippet,
                        source=self.name,
                        published_at=item.get("publishedDate"),
                    )
                )
            return results

        return await self.breaker.call(_do)
