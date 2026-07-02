from datetime import datetime

from app.config import get_settings
from app.core.logging import get_logger
from app.ingestion.parsers.csv_parser import parse_csv
from app.ingestion.parsers.docx_parser import parse_docx
from app.ingestion.parsers.html_parser import parse_html
from app.ingestion.parsers.pdf_parser import parse_pdf
from app.ingestion.parsers.text_parser import parse_text
from app.ingestion.parsers.xlsx_parser import parse_xlsx
from app.retrieval.chunking import chunk_text
from app.retrieval.embeddings import get_embedding_provider
from app.retrieval.sparse import to_sparse_vector
from app.vectorstore.qdrant_client import ensure_collection, upsert_chunks
from app.vectorstore.schema import ChunkPayload

logger = get_logger(__name__)

PARSERS = {
    "pdf": parse_pdf,
    "docx": parse_docx,
    "csv": parse_csv,
    "xlsx": parse_xlsx,
    "txt": parse_text,
    "md": parse_text,
    "html": parse_html,
}

CONNECTOR_AUTHORITY_WEIGHTS = {
    "upload": 1.0,
    "s3": 0.9,
    "azure_blob": 0.9,
    "gcs": 0.9,
    "web": 0.6,
    "slack": 0.5,
    "github": 0.8,
    "jira": 0.75,
}


async def ingest_raw_content(tenant_id: str, document_id: str, file_extension: str, raw_bytes: bytes, title: str, source_uri: str, source_type: str, connector_id: str | None = None) -> int:
    settings = get_settings()
    parser = PARSERS.get(file_extension.lower())
    if parser is None:
        raise ValueError(f"unsupported file type: {file_extension}")

    import inspect
    if inspect.iscoroutinefunction(parser):
        page_blocks = await parser(raw_bytes)
    else:
        page_blocks = parser(raw_bytes)

    all_chunks: list[str] = []
    all_pages: list[int | None] = []
    for text, page_number in page_blocks:
        pieces = chunk_text(text, settings.chunk_size_tokens, settings.chunk_overlap_tokens)
        all_chunks.extend(pieces)
        all_pages.extend([page_number] * len(pieces))

    if not all_chunks:
        return 0

    embedder = get_embedding_provider()
    vectors = await embedder.embed(all_chunks)
    await ensure_collection(tenant_id, len(vectors[0]))

    sparse_vectors = [to_sparse_vector(c) for c in all_chunks]
    authority = CONNECTOR_AUTHORITY_WEIGHTS.get(source_type, 0.7)
    now_iso = datetime.utcnow().isoformat()
    payloads = [
        ChunkPayload(
            tenant_id=tenant_id,
            document_id=document_id,
            chunk_index=i,
            text=chunk,
            source_type=source_type,
            source_uri=source_uri,
            title=title,
            created_at=now_iso,
            page_number=all_pages[i],
            connector_id=connector_id,
            authority_weight=authority,
        )
        for i, chunk in enumerate(all_chunks)
    ]

    await upsert_chunks(tenant_id, vectors, sparse_vectors, payloads)
    return len(all_chunks)
