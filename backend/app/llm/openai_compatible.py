import json
import time
from collections.abc import AsyncIterator

import httpx

from app.core.circuit_breaker import get_circuit_breaker
from app.core.metrics import llm_latency_seconds, llm_requests_total, tokens_used_total
from app.llm.base import LLMProvider, LLMResponse, Message, StreamChunk


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, name: str, api_key: str, base_url: str, default_headers: dict | None = None):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.breaker = get_circuit_breaker(f"llm:{name}")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", **self.default_headers}

    def _serialize_messages(self, messages: list[Message]) -> list[dict]:
        serialized = []
        for m in messages:
            if m.image_base64:
                serialized.append({
                    "role": m.role,
                    "content": [
                        {"type": "text", "text": m.content},
                        {"type": "image_url", "image_url": {"url": f"data:{m.image_media_type};base64,{m.image_base64}"}},
                    ],
                })
            else:
                serialized.append({"role": m.role, "content": m.content})
        return serialized

    async def complete(self, messages: list[Message], model: str, temperature: float = 0.3, max_tokens: int = 1024) -> LLMResponse:
        async def _do():
            start = time.monotonic()
            payload = {
                "model": model,
                "messages": self._serialize_messages(messages),
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            }
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            latency_ms = int((time.monotonic() - start) * 1000)
            usage = data.get("usage", {})
            llm_latency_seconds.labels(provider=self.name, model=model).observe(latency_ms / 1000)
            tokens_used_total.labels(provider=self.name, kind="prompt").inc(usage.get("prompt_tokens", 0))
            tokens_used_total.labels(provider=self.name, kind="completion").inc(usage.get("completion_tokens", 0))
            return LLMResponse(
                content=data["choices"][0]["message"]["content"] or "",
                provider=self.name,
                model=model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                latency_ms=latency_ms,
                raw=data,
            )

        try:
            result = await self.breaker.call(_do)
            llm_requests_total.labels(provider=self.name, model=model, status="success").inc()
            return result
        except Exception:
            llm_requests_total.labels(provider=self.name, model=model, status="error").inc()
            raise

    async def stream_complete(self, messages: list[Message], model: str, temperature: float = 0.3, max_tokens: int = 1024) -> AsyncIterator[StreamChunk]:
        self.breaker.check()
        start = time.monotonic()
        payload = {
            "model": model,
            "messages": self._serialize_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        prompt_tokens = 0
        completion_tokens = 0
        try:
            async with (
                httpx.AsyncClient(timeout=120.0) as client,
                client.stream("POST", f"{self.base_url}/chat/completions", headers=self._headers(), json=payload) as resp,
            ):
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break
                    if not data_str:
                        continue
                    chunk = json.loads(data_str)
                    usage = chunk.get("usage")
                    if usage:
                        prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
                        completion_tokens = usage.get("completion_tokens", completion_tokens)
                    choices = chunk.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {}).get("content") or ""
                    if delta:
                        yield StreamChunk(delta=delta, done=False)
        except Exception:
            self.breaker.record_failure()
            llm_requests_total.labels(provider=self.name, model=model, status="error").inc()
            raise
        self.breaker.record_success()
        llm_requests_total.labels(provider=self.name, model=model, status="success").inc()
        llm_latency_seconds.labels(provider=self.name, model=model).observe(time.monotonic() - start)
        tokens_used_total.labels(provider=self.name, kind="prompt").inc(prompt_tokens)
        tokens_used_total.labels(provider=self.name, kind="completion").inc(completion_tokens)
        yield StreamChunk(delta="", done=True, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
