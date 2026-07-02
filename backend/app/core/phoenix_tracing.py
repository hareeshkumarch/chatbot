from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any

from app.config import get_settings
from app.llm.base import Message

_phoenix_ready = False


def is_phoenix_enabled() -> bool:
    return get_settings().phoenix_enabled and _phoenix_ready


def mark_phoenix_ready() -> None:
    global _phoenix_ready
    _phoenix_ready = True


_phoenix_project_id = None


def _fetch_project_id_sync() -> str:
    global _phoenix_project_id
    if _phoenix_project_id:
        return _phoenix_project_id
    settings = get_settings()
    project_name = settings.phoenix_project_name
    import httpx
    try:
        with httpx.Client(timeout=2.0) as client:
            graphql_url = settings.phoenix_collector_endpoint.replace("/v1/traces", "/graphql")
            resp = client.post(graphql_url, json={"query": "{ projects { edges { node { id name } } } }"})
            if resp.status_code == 200:
                edges = resp.json().get("data", {}).get("projects", {}).get("edges", [])
                for edge in edges:
                    node = edge.get("node", {})
                    if node.get("name") == project_name:
                        _phoenix_project_id = node.get("id")
                        return _phoenix_project_id
    except Exception:
        pass
    return "UHJvamVjdDoy"


def phoenix_trace_url(conversation_id: str) -> str | None:
    if not is_phoenix_enabled():
        return None
    settings = get_settings()
    base = settings.phoenix_ui_url.rstrip("/")
    project_id = _fetch_project_id_sync()
    return f"{base}/projects/{project_id}/spans?sessionId={conversation_id}"


def _messages_preview(messages: list[Message], limit: int = 4000) -> str:
    payload = [{"role": message.role, "content": message.content[:800]} for message in messages]
    text = json.dumps(payload, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + "…"


@asynccontextmanager
async def trace_chat_turn(
    *,
    conversation_id: str,
    query: str,
    tenant_id: str,
    user_id: str,
):
    if not is_phoenix_enabled():
        yield None
        return

    from openinference.instrumentation import using_session
    from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    tracer = trace.get_tracer("enterprise-ai-platform.chat")
    with using_session(conversation_id):
        with tracer.start_as_current_span(
            "chat.turn",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                SpanAttributes.INPUT_VALUE: query,
                SpanAttributes.SESSION_ID: conversation_id,
                "tenant.id": tenant_id,
                "user.id": user_id,
            },
        ) as span:
            try:
                yield span
            except Exception as exc:
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                span.record_exception(exc)
                raise
            else:
                span.set_status(Status(StatusCode.OK))


@asynccontextmanager
async def trace_llm_call(
    *,
    task: str,
    messages: list[Message],
    provider: str | None = None,
    model: str | None = None,
):
    if not is_phoenix_enabled():
        yield None
        return

    from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    tracer = trace.get_tracer("enterprise-ai-platform.llm")
    attributes: dict[str, Any] = {
        SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.LLM.value,
        SpanAttributes.LLM_INVOCATION_PARAMETERS: json.dumps({"task": task}),
        SpanAttributes.INPUT_VALUE: _messages_preview(messages),
        "llm.task": task,
    }
    if provider:
        attributes[SpanAttributes.LLM_PROVIDER] = provider
    if model:
        attributes[SpanAttributes.LLM_MODEL_NAME] = model

    with tracer.start_as_current_span(f"llm.{task}", attributes=attributes) as span:
        try:
            yield span
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise


def annotate_llm_result(
    span: Any,
    *,
    output: str,
    provider: str | None,
    model: str | None,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    if span is None:
        return
    from openinference.semconv.trace import SpanAttributes

    span.set_attribute(SpanAttributes.OUTPUT_VALUE, output[:8000])
    if provider:
        span.set_attribute(SpanAttributes.LLM_PROVIDER, provider)
    if model:
        span.set_attribute(SpanAttributes.LLM_MODEL_NAME, model)
    span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_PROMPT, max(0, prompt_tokens))
    span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_COMPLETION, max(0, completion_tokens))
    span.set_attribute(SpanAttributes.LLM_TOKEN_COUNT_TOTAL, max(0, prompt_tokens) + max(0, completion_tokens))


@asynccontextmanager
async def trace_orchestration_node(node_name: str, intent: str | None = None):
    if not is_phoenix_enabled():
        yield None
        return

    from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    tracer = trace.get_tracer("enterprise-ai-platform.orchestration")
    attributes = {
        SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
        "orchestration.node": node_name,
    }
    if intent:
        attributes["orchestration.intent"] = intent

    with tracer.start_as_current_span(f"node.{node_name}", attributes=attributes) as span:
        try:
            yield span
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise
        else:
            span.set_status(Status(StatusCode.OK))
