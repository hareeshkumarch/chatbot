from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models import Conversation
from app.db.models import Message as MessageRow

HISTORY_LIMIT = 20


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_conversations(self, tenant_id: str, user_id: str) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.tenant_id == tenant_id, Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(100)
        )
        return list(result.scalars().all())

    async def get_owned_conversation(self, conversation_id: str, tenant_id: str) -> Conversation:
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.tenant_id == tenant_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise NotFoundError("conversation not found")
        return conversation

    async def create_conversation(self, tenant_id: str, user_id: str, title: str) -> Conversation:
        conversation = Conversation(tenant_id=tenant_id, user_id=user_id, title=title)
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get_or_create_conversation(self, tenant_id: str, user_id: str, conversation_id: str | None, seed_title: str) -> Conversation:
        if conversation_id:
            return await self.get_owned_conversation(conversation_id, tenant_id)
        return await self.create_conversation(tenant_id, user_id, seed_title[:80])

    async def get_messages(self, conversation_id: str) -> list[MessageRow]:
        result = await self.session.execute(
            select(MessageRow).where(MessageRow.conversation_id == conversation_id).order_by(MessageRow.created_at.asc())
        )
        return list(result.scalars().all())

    async def load_recent_history(self, conversation_id: str, limit: int = HISTORY_LIMIT) -> list[MessageRow]:
        result = await self.session.execute(
            select(MessageRow)
            .where(MessageRow.conversation_id == conversation_id)
            .order_by(MessageRow.created_at.desc())
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))

    async def record_user_message(self, conversation_id: str, content: str) -> MessageRow:
        message = MessageRow(conversation_id=conversation_id, role="user", content=content)
        self.session.add(message)
        await self.session.commit()
        return message

    async def record_assistant_message(
        self,
        conversation_id: str,
        content: str,
        citations: list[dict],
        provider_used: str | None,
        model_used: str | None,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        confidence: float | None,
    ) -> MessageRow:
        message = MessageRow(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            citations=citations,
            provider_used=provider_used,
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            confidence=confidence,
        )
        self.session.add(message)
        await self.session.commit()
        return message

    async def delete_conversation(self, conversation: Conversation) -> None:
        await self.session.execute(delete(MessageRow).where(MessageRow.conversation_id == conversation.id))
        await self.session.delete(conversation)
        await self.session.commit()
