import asyncio
import base64
from datetime import datetime

from sqlalchemy import select

from app.connectors.loader import instantiate_connector
from app.core.logging import get_logger
from app.db.base import async_session_maker
from app.db.models import Connector, Document
from app.ingestion.pipeline import ingest_raw_content
from app.vectorstore.qdrant_client import delete_by_document
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


async def _ingest_document(
    document_id: str,
    file_extension: str,
    raw_bytes: bytes,
    title: str,
    source_uri: str,
    source_type: str,
    connector_id: str | None,
) -> None:
    async with async_session_maker() as session:
        result = await session.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if document is None:
            logger.warning(f"document {document_id} not found, skipping ingestion")
            return

        document.status = "processing"
        await session.commit()

        try:
            await delete_by_document(document.tenant_id, document.id)
            chunk_count = await ingest_raw_content(
                tenant_id=document.tenant_id,
                document_id=document.id,
                file_extension=file_extension,
                raw_bytes=raw_bytes,
                title=title,
                source_uri=source_uri,
                source_type=source_type,
                connector_id=connector_id,
            )
        except Exception as exc:
            logger.error(f"ingestion failed for document {document_id}: {exc}")
            document.status = "failed"
            document.error_message = str(exc)[:2000]
            await session.commit()
            return

        document.status = "indexed"
        document.chunk_count = chunk_count
        document.indexed_at = datetime.utcnow()
        await session.commit()


@celery_app.task(name="ingest_document", bind=True, max_retries=2)
def ingest_document_task(
    self,
    document_id: str,
    file_extension: str,
    raw_bytes_b64: str,
    title: str,
    source_uri: str,
    source_type: str,
    connector_id: str | None = None,
) -> None:
    raw_bytes = base64.b64decode(raw_bytes_b64)
    asyncio.run(_ingest_document(document_id, file_extension, raw_bytes, title, source_uri, source_type, connector_id))


async def _sync_connector(connector_id: str) -> None:
    async with async_session_maker() as session:
        result = await session.execute(select(Connector).where(Connector.id == connector_id))
        connector_row = result.scalar_one_or_none()
        if connector_row is None:
            logger.warning(f"connector {connector_id} not found, skipping sync")
            return

        try:
            instance = await instantiate_connector(session, connector_row)
            contents = await instance.sync()
        except Exception as exc:
            logger.error(f"connector sync failed for {connector_id}: {exc}")
            connector_row.status = "error"
            await session.commit()
            return

        for content in contents:
            existing = await session.execute(
                select(Document).where(Document.connector_id == connector_id, Document.source_uri == content.source_uri)
            )
            document = existing.scalar_one_or_none()
            if document is None:
                document = Document(
                    tenant_id=connector_row.tenant_id,
                    connector_id=connector_id,
                    source_type=connector_row.type,
                    source_uri=content.source_uri,
                    title=content.title,
                    status="processing",
                    size_bytes=len(content.raw_bytes),
                )
                session.add(document)
                await session.flush()
            else:
                document.status = "processing"
                document.size_bytes = len(content.raw_bytes)
                document.error_message = None
            await session.commit()

            try:
                await delete_by_document(connector_row.tenant_id, document.id)
                chunk_count = await ingest_raw_content(
                    tenant_id=connector_row.tenant_id,
                    document_id=document.id,
                    file_extension=content.file_extension,
                    raw_bytes=content.raw_bytes,
                    title=content.title,
                    source_uri=content.source_uri,
                    source_type=connector_row.type,
                    connector_id=connector_id,
                )
                document.status = "indexed"
                document.chunk_count = chunk_count
                document.indexed_at = datetime.utcnow()
            except Exception as exc:
                logger.error(f"ingestion failed for synced document {content.source_uri}: {exc}")
                document.status = "failed"
                document.error_message = str(exc)[:2000]
            await session.commit()

        connector_row.status = "connected"
        connector_row.last_synced_at = datetime.utcnow()
        await session.commit()


@celery_app.task(name="sync_connector", bind=True, max_retries=2)
def sync_connector_task(self, connector_id: str) -> None:
    asyncio.run(_sync_connector(connector_id))
