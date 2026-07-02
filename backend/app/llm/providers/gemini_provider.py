import time
from collections.abc import AsyncIterator

import httpx

from app.core.circuit_breaker import get_circuit_breaker
from app.core.metrics import llm_latency_seconds, llm_requests_total, tokens_used_total
from app.llm.base import LLMProvider, LLMResponse, Message, StreamChunk


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str):
        self.name = "gemini"
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.breaker = get_circuit_breaker("llm:gemini")

    def _to_contents(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        system_parts = [m.content for m in messages if m.role == "system"]
        contents = []
        for m in messages:
            if m.role == "system":
                continue
            role = "model" if m.role == "assistant" else "user"
            if m.image_base64:
                parts = [{"inline_data": {"mime_type": m.image_media_type, "data": m.image_base64}}, {"text": m.content}]
            else:
                parts = [{"text": m.content}]
            contents.append({"role": role, "parts": parts})
        system = "\n\n".join(system_parts) if system_parts else None
        return system, contents

    async def complete(self, messages: list[Message], model: str, temperature: float = 0.3, max_tokens: int = 1024) -> LLMResponse:
        async def _do():
            start = time.monotonic()
            system, contents = self._to_contents(messages)
            payload = {"contents": contents, "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
            if system:
                payload["systemInstruction"] = {"parts": [{"text": system}]}
            headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(f"{self.base_url}/models/{model}:generateContent", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            latency_ms = int((time.monotonic() - start) * 1000)
            usage = data.get("usageMetadata", {})
            candidates = data.get("candidates", [])
            text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)
            llm_latency_seconds.labels(provider=self.name, model=model).observe(latency_ms / 1000)
            tokens_used_total.labels(provider=self.name, kind="prompt").inc(usage.get("promptTokenCount", 0))
            tokens_used_total.labels(provider=self.name, kind="completion").inc(usage.get("candidatesTokenCount", 0))
            return LLMResponse(
                content=text,
                provider=self.name,
                model=model,
                prompt_tokens=usage.get("promptTokenCount", 0),
                completion_tokens=usage.get("candidatesTokenCount", 0),
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
        system, contents = self._to_contents(messages)
        payload = {"contents": contents, "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        url = f"{self.base_url}/models/{model}:streamGenerateContent?alt=sse"
        prompt_tokens = 0
        completion_tokens = 0
        try:
            async with (
                httpx.AsyncClient(timeout=120.0) as client,
                client.stream("POST", url, headers=headers, json=payload) as resp,
            ):
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data_str = line[len("data:"):].strip()
                    if not data_str:
                        continue
                    chunk = jsonlib.loads(data_str)
                    usage = chunk.get("usageMetadata")
                    if usage:
                        prompt_tokens = usage.get("promptTokenCount", prompt_tokens)
                        completion_tokens = usage.get("candidatesTokenCount", completion_tokens)
                    candidates = chunk.get("candidates", [])
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts)
                    if text:
                        yield StreamChunk(delta=text, done=False)
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
