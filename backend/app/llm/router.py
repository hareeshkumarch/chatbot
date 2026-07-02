from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import StrEnum

from app.core.circuit_breaker import CircuitBreakerOpenError
from app.core.exceptions import ProviderUnavailableError
from app.core.logging import get_logger
from app.core.phoenix_tracing import annotate_llm_result, trace_llm_call
from app.llm.base import LLMResponse, Message, StreamChunk
from app.llm.registry import DEFAULT_MODELS, available_providers, get_provider

logger = get_logger(__name__)


class TaskType(StrEnum):
    QUERY_CLASSIFICATION = "query_classification"
    QUERY_REWRITE = "query_rewrite"
    HYDE = "hyde"
    RETRIEVAL_SYNTHESIS = "retrieval_synthesis"
    CONNECTOR_SYNTHESIS = "connector_synthesis"
    SQL_GENERATION = "sql_generation"
    SUMMARIZATION = "summarization"
    VERIFICATION = "verification"
    GENERAL_CHAT = "general_chat"
    REPORT_STRUCTURING = "report_structuring"


TASK_ROUTING_TABLE: dict[TaskType, list[str]] = {
    TaskType.QUERY_CLASSIFICATION: ["groq", "gemini", "moonshot", "openai", "anthropic", "grok"],
    TaskType.QUERY_REWRITE: ["groq", "gemini", "moonshot", "openai", "anthropic", "grok"],
    TaskType.HYDE: ["groq", "gemini", "openai", "anthropic", "moonshot", "grok"],
    TaskType.RETRIEVAL_SYNTHESIS: ["anthropic", "openai", "gemini", "grok", "moonshot", "groq"],
    TaskType.CONNECTOR_SYNTHESIS: ["anthropic", "openai", "gemini", "grok", "moonshot", "groq"],
    TaskType.SQL_GENERATION: ["anthropic", "openai", "moonshot", "gemini", "grok", "groq"],
    TaskType.SUMMARIZATION: ["gemini", "anthropic", "openai", "groq", "moonshot", "grok"],
    TaskType.VERIFICATION: ["groq", "gemini", "moonshot", "anthropic", "openai", "grok"],
    TaskType.GENERAL_CHAT: ["anthropic", "openai", "gemini", "grok", "moonshot", "groq"],
    TaskType.REPORT_STRUCTURING: ["anthropic", "openai", "gemini", "grok", "moonshot", "groq"],
}

TASK_DEFAULT_TEMPERATURE: dict[TaskType, float] = {
    TaskType.QUERY_CLASSIFICATION: 0.0,
    TaskType.QUERY_REWRITE: 0.2,
    TaskType.HYDE: 0.4,
    TaskType.RETRIEVAL_SYNTHESIS: 0.3,
    TaskType.CONNECTOR_SYNTHESIS: 0.3,
    TaskType.SQL_GENERATION: 0.0,
    TaskType.SUMMARIZATION: 0.3,
    TaskType.VERIFICATION: 0.0,
    TaskType.GENERAL_CHAT: 0.6,
    TaskType.REPORT_STRUCTURING: 0.2,
}


@dataclass
class RouteDecision:
    provider: str
    model: str
    fallback_chain: list[str]


class ModelRouter:
    def resolve(self, task: TaskType, explicit_provider: str | None = None, explicit_model: str | None = None, tenant_preferred_order: list[str] | None = None) -> RouteDecision:
        configured = set(available_providers())
        if not configured:
            raise ProviderUnavailableError("no LLM providers are configured")
        if explicit_provider:
            if explicit_provider not in configured:
                raise ProviderUnavailableError(f"provider '{explicit_provider}' is not configured")
            chain = [explicit_provider] + [p for p in TASK_ROUTING_TABLE[task] if p != explicit_provider and p in configured]
            model = explicit_model or DEFAULT_MODELS[explicit_provider]
            return RouteDecision(provider=explicit_provider, model=model, fallback_chain=chain)
        candidate_order = tenant_preferred_order or TASK_ROUTING_TABLE[task]
        chain = [p for p in candidate_order if p in configured]
        if not chain:
            chain = list(configured)
        primary = chain[0]
        return RouteDecision(provider=primary, model=DEFAULT_MODELS[primary], fallback_chain=chain)

    async def complete_with_fallback(self, task: TaskType, messages: list[Message], explicit_provider: str | None = None, explicit_model: str | None = None, temperature: float | None = None, max_tokens: int = 1024) -> LLMResponse:
        decision = self.resolve(task, explicit_provider, explicit_model)
        temp = temperature if temperature is not None else TASK_DEFAULT_TEMPERATURE[task]
        last_error: Exception | None = None
        async with trace_llm_call(task=task.value, messages=messages, provider=decision.provider, model=decision.model) as span:
            for provider_name in decision.fallback_chain:
                provider = get_provider(provider_name)
                model = decision.model if provider_name == decision.provider else DEFAULT_MODELS[provider_name]
                try:
                    response = await provider.complete(messages, model=model, temperature=temp, max_tokens=max_tokens)
                    annotate_llm_result(
                        span,
                        output=response.content,
                        provider=response.provider,
                        model=response.model,
                        prompt_tokens=response.prompt_tokens,
                        completion_tokens=response.completion_tokens,
                    )
                    return response
                except CircuitBreakerOpenError as exc:
                    logger.warning(f"circuit open for {provider_name}, trying next")
                    last_error = exc
                    continue
                except Exception as exc:
                    logger.warning(f"provider {provider_name} failed: {exc}")
                    last_error = exc
                    continue
            raise ProviderUnavailableError(f"all providers in fallback chain failed: {last_error}")

    async def stream_with_fallback(self, task: TaskType, messages: list[Message], explicit_provider: str | None = None, explicit_model: str | None = None, temperature: float | None = None, max_tokens: int = 1024) -> AsyncIterator[StreamChunk]:
        decision = self.resolve(task, explicit_provider, explicit_model)
        temp = temperature if temperature is not None else TASK_DEFAULT_TEMPERATURE[task]
        last_error: Exception | None = None
        async with trace_llm_call(task=task.value, messages=messages, provider=decision.provider, model=decision.model) as span:
            output_parts: list[str] = []
            for provider_name in decision.fallback_chain:
                provider = get_provider(provider_name)
                model = decision.model if provider_name == decision.provider else DEFAULT_MODELS[provider_name]
                try:
                    started = False
                    async for chunk in provider.stream_complete(messages, model=model, temperature=temp, max_tokens=max_tokens):
                        started = True
                        chunk.provider = provider_name
                        chunk.model = model
                        if chunk.delta:
                            output_parts.append(chunk.delta)
                        if chunk.done:
                            annotate_llm_result(
                                span,
                                output="".join(output_parts),
                                provider=chunk.provider,
                                model=chunk.model,
                                prompt_tokens=chunk.prompt_tokens,
                                completion_tokens=chunk.completion_tokens,
                            )
                        yield chunk
                    return
                except Exception as exc:
                    if started:
                        raise
                    logger.warning(f"stream provider {provider_name} failed before first chunk: {exc}")
                    last_error = exc
                    continue
            raise ProviderUnavailableError(f"all providers in fallback chain failed: {last_error}")


router = ModelRouter()
