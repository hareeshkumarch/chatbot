import httpx

from app.core.circuit_breaker import get_circuit_breaker
from app.core.logging import get_logger
from app.intelligence.base import AnsweredResult, AnswerProvider

logger = get_logger(__name__)


class PerplexityProvider(AnswerProvider):
    name = "perplexity"
    base_url = "https://api.perplexity.ai"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.breaker = get_circuit_breaker("intel:perplexity")

    async def answer(self, query: str) -> AnsweredResult:
        async def _do() -> AnsweredResult:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": query}],
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])
            return AnsweredResult(answer=content, citations=citations)

        return await self.breaker.call(_do)
