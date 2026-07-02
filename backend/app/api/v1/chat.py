import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.common import raise_http_from_app_error
from app.core.exceptions import AppError
from app.core.limits import CONVERSATION_TITLE_MAX_LENGTH, MAX_CONNECTOR_IDS, MESSAGE_MAX_LENGTH
from app.dependencies import AuthContext, get_current_user, get_db
from app.services.chat_orchestrator import (
    ChatDoneEvent,
    ChatErrorEvent,
    ChatOrchestrator,
    ChatReplaceEvent,
    ChatStartEvent,
    ChatTokenEvent,
    ChatTurnRequest,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=CONVERSATION_TITLE_MAX_LENGTH)


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: list[dict]
    provider_used: str | None
    model_used: str | None
    confidence: float | None
    created_at: str


class ChatStreamRequestBody(BaseModel):
    message: str = Field(min_length=1, max_length=MESSAGE_MAX_LENGTH)
    conversation_id: str | None = None
    connector_ids: list[str] | None = Field(default=None, max_length=MAX_CONNECTOR_IDS)
    provider: str | None = None
    model: str | None = None

    @field_validator("message")
    @classmethod
    def _message_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message cannot be empty or whitespace")
        return stripped

    @field_validator("connector_ids")
    @classmethod
    def _dedupe_connector_ids(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        seen: set[str] = set()
        result: list[str] = []
        for item in value:
            if item and item not in seen:
                seen.add(item)
                result.append(item)
        return result


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreateRequest,
    auth: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ConversationOut:
    service = ChatService(session)
    conversation = await service.create_conversation(auth.tenant_id, auth.user_id, payload.title or "New conversation")
    await session.commit()
    return ConversationOut(id=conversation.id, title=conversation.title, created_at=conversation.created_at.isoformat())


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    auth: AuthContext = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> list[ConversationOut]:
    service = ChatService(session)
    conversations = await service.list_conversations(auth.tenant_id, auth.user_id)
    return [ConversationOut(id=c.id, title=c.title, created_at=c.created_at.isoformat()) for c in conversations]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: str,
    auth: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[MessageOut]:
    service = ChatService(session)
    try:
        await service.get_owned_conversation(conversation_id, auth.tenant_id)
    except AppError as exc:
        raise_http_from_app_error(exc)
    messages = await service.get_messages(conversation_id)
    return [
        MessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            citations=m.citations,
            provider_used=m.provider_used,
            model_used=m.model_used,
            confidence=m.confidence,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    auth: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = ChatService(session)
    try:
        conversation = await service.get_owned_conversation(conversation_id, auth.tenant_id)
    except AppError as exc:
        raise_http_from_app_error(exc)
    await service.delete_conversation(conversation)


@router.post("/stream")
async def stream_chat(
    payload: ChatStreamRequestBody,
    auth: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    if not payload.message.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="message cannot be empty")

    service = ChatService(session)
    orchestrator = ChatOrchestrator(service)
    turn_request = ChatTurnRequest(
        tenant_id=auth.tenant_id,
        user_id=auth.user_id,
        message=payload.message,
        conversation_id=payload.conversation_id,
        connector_ids=payload.connector_ids,
        provider=payload.provider,
        model=payload.model,
    )

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for event in orchestrator.run_turn(turn_request):
                if isinstance(event, ChatStartEvent):
                    yield _sse("start", {"conversation_id": event.conversation_id, "user_message_id": event.user_message_id})
                elif isinstance(event, ChatTokenEvent):
                    yield _sse("token", {"delta": event.delta})
                elif isinstance(event, ChatReplaceEvent):
                    yield _sse("replace", {"content": event.content})
                elif isinstance(event, ChatErrorEvent):
                    yield _sse("error", {"message": event.message})
                elif isinstance(event, ChatDoneEvent):
                    yield _sse("done", {
                        "message_id": event.message_id,
                        "conversation_id": event.conversation_id,
                        "citations": event.citations,
                        "provider": event.provider,
                        "model": event.model,
                        "verified": event.verified,
                        "confidence": event.confidence,
                        "error": event.error,
                        "plan": event.plan,
                        "llm_calls": event.llm_calls,
                        "blocks": event.blocks,
                        "prompt_tokens": event.prompt_tokens,
                        "completion_tokens": event.completion_tokens,
                        "cost_usd": event.cost_usd,
                        "latency_ms": event.latency_ms,
                        "query_log_id": event.query_log_id,
                        "phoenix_trace_url": event.phoenix_trace_url,
                    })
        except AppError as exc:
            yield _sse("error", {"message": exc.message})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
