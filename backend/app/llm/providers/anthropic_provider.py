import time
from collections.abc import AsyncIterator

import httpx

from app.core.circuit_breaker import get_circuit_breaker
from app.core.metrics import llm_latency_seconds, llm_requests_total, tokens_used_total
from app.llm.base import LLMProvider, LLMResponse, Message, StreamChunk


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str, api_version: str):
        self.name = "anthropic"
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.breaker = get_circuit_breaker("llm:anthropic")

    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }

    def _split_system(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        system_parts = [m.content for m in messages if m.role == "system"]
        rest = []
        for m in messages:
            if m.role == "system":
                continue
            if m.image_base64:
                rest.append({
                    "role": m.role,
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": m.image_media_type, "data": m.image_base64}},
                        {"type": "text", "text": m.content},
                    ],
                })
            else:
                rest.append({"role": m.role, "content": m.content})
        system = "\n\n".join(system_parts) if system_parts else None
        return system, rest

    async def complete(self, messages: list[Message], model: str, temperature: float = 0.3, max_tokens: int = 1024) -> LLMResponse:
        async def _do():
            start = time.monotonic()
            system, rest = self._split_system(messages)
            payload = {"model": model, "messages": rest, "max_tokens": max_tokens, "temperature": temperature}
            if system:
                payload["system"] = system
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self.base_url}/v1/messages", headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            latency_ms = int((time.monotonic() - start) * 1000)
            usage = data.get("usage", {})
            text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
            llm_latency_seconds.labels(provider=self.name, model=model).observe(latency_ms / 1000)
            tokens_used_total.labels(provider=self.name, kind="prompt").inc(usage.get("input_tokens", 0))
            tokens_used_total.labels(provider=self.name, kind="completion").inc(usage.get("output_tokens", 0))
            return LLMResponse(
                content=text,
                provider=self.name,
                model=model,
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
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
        import json as jsonlib
        self.breaker.check()
        start = time.monotonic()
        system, rest = self._split_system(messages)
        payload = {"model": model, "messages": rest, "max_tokens": max_tokens, "temperature": temperature, "stream": True}
        if system:
            payload["system"] = system
        prompt_tokens = 0
        completion_tokens = 0
        try:
            async with (
                httpx.AsyncClient(timeout=120.0) as client,
                client.stream("POST", f"{self.base_url}/v1/messages", headers=self._headers(), json=payload) as resp,
            ):
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data_str = line[len("data:"):].strip()
                    if not data_str:
                        continue
                    event = jsonlib.loads(data_str)
                    event_type = event.get("type")
                    if event_type == "message_start":
                        prompt_tokens = event.get("message", {}).get("usage", {}).get("input_tokens", 0)
                    elif event_type == "content_block_delta":
                        delta_text = event.get("delta", {}).get("text", "")
                        if delta_text:
                            yield StreamChunk(delta=delta_text, done=False)
                    elif event_type == "message_delta":
                        completion_tokens = event.get("usage", {}).get("output_tokens", completion_tokens)
                    elif event_type == "message_stop":
                        break
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
