import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

from app.analytics.tracker import log_query, summarize_llm_calls
from app.connectors.loader import build_active_connectors
from app.core.logging import get_logger
from app.core.phoenix_tracing import phoenix_trace_url, trace_chat_turn
from app.llm.base import Message
from app.llm.router import router as llm_router
from app.orchestration.answer_formatting import (
    build_synthesis_plan,
    extract_confidence,
    extract_document_chunk_count,
    extract_retrieval_strategy,
    extract_top_relevance_score,
    format_plan_results,
)
from app.orchestration.graph import retrieval_graph
from app.orchestration.state import GraphContext, GraphState
from app.orchestration.telemetry import record_llm_call
from app.orchestration.verification import check_grounding
from app.services.chat_service import ChatService

logger = get_logger(__name__)

MAX_VERIFICATION_RETRIES = 1


@dataclass
class ChatStartEvent:
    conversation_id: str
    user_message_id: str


@dataclass
class ChatTokenEvent:
    delta: str


@dataclass
class ChatErrorEvent:
    message: str


@dataclass
class ChatDoneEvent:
    message_id: str
    conversation_id: str
    citations: list[dict]
    provider: str | None
    model: str | None
    verified: bool
    confidence: float | None
    error: bool
    plan: list[dict]
    llm_calls: list[dict]
    blocks: list[dict]
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_ms: int
    query_log_id: str
    phoenix_trace_url: str | None = None


@dataclass
class ChatReplaceEvent:
    content: str


ChatEvent = ChatStartEvent | ChatTokenEvent | ChatReplaceEvent | ChatErrorEvent | ChatDoneEvent


@dataclass
class ChatTurnRequest:
    tenant_id: str
    user_id: str
    message: str
    conversation_id: str | None = None
    connector_ids: list[str] | None = None
    provider: str | None = None
    model: str | None = None


@dataclass
class _TurnAccumulator:
    full_text: str = ""
    provider_used: str | None = None
    model_used: str | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    citations: list[dict] = field(default_factory=list)
    blocks: list[dict] = field(default_factory=list)
    error_occurred: bool = False


class ChatOrchestrator:
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    async def run_turn(self, request: ChatTurnRequest) -> AsyncGenerator[ChatEvent, None]:
        start = time.monotonic()

        conversation = await self.chat_service.get_or_create_conversation(
            request.tenant_id, request.user_id, request.conversation_id, request.message
        )
        history_rows = await self.chat_service.load_recent_history(conversation.id)
        history = [Message(role=row.role, content=row.content) for row in history_rows if row.role in ("user", "assistant")]
        user_message = await self.chat_service.record_user_message(conversation.id, request.message)

        yield ChatStartEvent(conversation_id=conversation.id, user_message_id=user_message.id)

        async with trace_chat_turn(
            conversation_id=conversation.id,
            query=request.message,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
        ):
            sql_connector, active_connectors = await build_active_connectors(
                self.chat_service.session, request.tenant_id, request.connector_ids
            )
            graph_context = GraphContext(
                sql_connector=sql_connector,
                active_connectors=active_connectors,
                explicit_provider=request.provider,
                explicit_model=request.model,
            )
            initial_state: GraphState = {
                "tenant_id": request.tenant_id,
                "connector_ids": request.connector_ids or [],
                "query": request.message,
                "history": history,
                "llm_calls": [],
            }

            try:
                state_after_retrieval = await retrieval_graph.ainvoke(initial_state, context=graph_context)
            except Exception as exc:
                logger.error(f"retrieval phase failed: {exc}")
                yield ChatErrorEvent(message="failed to process the request")
                return

            llm_calls = state_after_retrieval.get("llm_calls", [])
            plan = state_after_retrieval.get("plan", [])
            plan_results = state_after_retrieval.get("plan_results") or []
            context_text, _, structured_blocks = format_plan_results(plan_results) if plan_results else ("", [], [])

            plan_ctx = build_synthesis_plan(state_after_retrieval, retry=False)
            accumulator = _TurnAccumulator(citations=plan_ctx.citations, blocks=plan_ctx.blocks or structured_blocks)
            verified = True
            verify_reason: str | None = None

            for attempt in range(MAX_VERIFICATION_RETRIES + 1):
                if attempt > 0:
                    plan_ctx = build_synthesis_plan(state_after_retrieval, retry=True, retry_reason=verify_reason)
                    accumulator = _TurnAccumulator(citations=plan_ctx.citations, blocks=plan_ctx.blocks or structured_blocks)

                if plan_ctx.skip_llm:
                    accumulator.full_text = plan_ctx.fallback_answer
                    if attempt == 0:
                        yield ChatTokenEvent(delta=accumulator.full_text)
                else:
                    async for event in self._stream_synthesis(
                        plan_ctx,
                        request,
                        accumulator,
                        yield_tokens=attempt == 0,
                    ):
                        yield event
                    if attempt > 0:
                        yield ChatReplaceEvent(content=accumulator.full_text)
                    llm_calls = record_llm_call(
                        llm_calls,
                        "synthesis",
                        accumulator.provider_used,
                        accumulator.model_used,
                        accumulator.prompt_tokens,
                        accumulator.completion_tokens,
                    )

                verified, llm_calls, verify_reason = await check_grounding(
                    accumulator.full_text,
                    context_text,
                    state_after_retrieval.get("intent"),
                    request.provider,
                    request.model,
                    llm_calls,
                )
                if verified or plan_ctx.skip_llm or attempt >= MAX_VERIFICATION_RETRIES:
                    break

            latency_ms = int((time.monotonic() - start) * 1000)
            confidence = extract_confidence(plan_results)
            prompt_tokens_total, completion_tokens_total, cost_usd = summarize_llm_calls(llm_calls)

            assistant_message = await self.chat_service.record_assistant_message(
                conversation.id,
                accumulator.full_text,
                accumulator.citations,
                accumulator.provider_used,
                accumulator.model_used,
                prompt_tokens_total,
                completion_tokens_total,
                latency_ms,
                confidence,
            )

            query_log = await log_query(
                self.chat_service.session,
                tenant_id=request.tenant_id,
                conversation_id=conversation.id,
                query_text=request.message,
                plan=plan,
                retrieval_strategy=extract_retrieval_strategy(plan_results),
                retrieved_chunk_count=extract_document_chunk_count(plan_results),
                top_relevance_score=extract_top_relevance_score(plan_results),
                confidence=confidence or 0.0,
                provider=accumulator.provider_used,
                model=accumulator.model_used,
                llm_calls=llm_calls,
                latency_ms=latency_ms,
            )

        yield ChatDoneEvent(
            message_id=assistant_message.id,
            conversation_id=conversation.id,
            citations=accumulator.citations,
            provider=accumulator.provider_used,
            model=accumulator.model_used,
            verified=verified,
            confidence=confidence,
            error=accumulator.error_occurred,
            plan=plan,
            llm_calls=llm_calls,
            blocks=accumulator.blocks,
            prompt_tokens=prompt_tokens_total,
            completion_tokens=completion_tokens_total,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            query_log_id=query_log.id,
            phoenix_trace_url=phoenix_trace_url(conversation.id),
        )

    async def _stream_synthesis(
        self,
        plan_ctx,
        request: ChatTurnRequest,
        accumulator: _TurnAccumulator,
        *,
        yield_tokens: bool = True,
    ) -> AsyncGenerator[ChatEvent, None]:
        if not yield_tokens:
            accumulator.full_text = ""
            accumulator.error_occurred = False
        try:
            async for chunk in llm_router.stream_with_fallback(
                plan_ctx.task_type,
                plan_ctx.messages,
                explicit_provider=request.provider,
                explicit_model=request.model,
                max_tokens=plan_ctx.max_tokens,
            ):
                if chunk.delta:
                    accumulator.full_text += chunk.delta
                    if yield_tokens:
                        yield ChatTokenEvent(delta=chunk.delta)
                if chunk.done:
                    accumulator.provider_used = chunk.provider
                    accumulator.model_used = chunk.model
                    accumulator.prompt_tokens = chunk.prompt_tokens
                    accumulator.completion_tokens = chunk.completion_tokens
        except Exception as exc:
            logger.error(f"synthesis stream failed: {exc}")
            accumulator.error_occurred = True
            if not accumulator.full_text:
                accumulator.full_text = "The answer could not be generated because all configured LLM providers are unavailable."
            yield ChatErrorEvent(message="an LLM provider error occurred, showing partial or fallback output")
