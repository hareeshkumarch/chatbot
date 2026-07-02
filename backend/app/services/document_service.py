from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models import Document
from app.vectorstore.qdrant_client import delete_by_document

ALLOWED_EXTENSIONS = {"pdf", "docx", "csv", "xlsx", "txt", "md", "html"}


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_documents(self, tenant_id: str) -> list[Document]:
        result = await self.session.execute(
            select(Document).where(Document.tenant_id == tenant_id).order_by(Document.created_at.desc()).limit(200)
        )
        return list(result.scalars().all())

    async def get_owned_document(self, document_id: str, tenant_id: str) -> Document:
        result = await self.session.execute(select(Document).where(Document.id == document_id, Document.tenant_id == tenant_id))
        document = result.scalar_one_or_none()
        if document is None:
            raise NotFoundError("document not found")
        return document

    async def create_pending_upload(self, tenant_id: str, filename: str, size_bytes: int) -> Document:
        document = Document(
            tenant_id=tenant_id,
            source_type="upload",
            source_uri=f"upload://{filename}",
            title=filename,
            status="pending",
            size_bytes=size_bytes,
        )
        self.session.add(document)
        await self.session.commit()
        return document

    async def mark_queue_failed(self, document: Document, reason: str) -> None:
        document.status = "failed"
        document.error_message = reason
        await self.session.commit()

    async def delete_document(self, tenant_id: str, document: Document) -> None:
        await delete_by_document(tenant_id, document.id)
        await self.session.delete(document)
        await self.session.commit()
