import base64

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.common import raise_http_from_app_error
from app.config import get_settings
from app.core.exceptions import AppError
from app.dependencies import AuthContext, get_current_user, get_db
from app.services.document_service import ALLOWED_EXTENSIONS, DocumentService
from app.workers.tasks import ingest_document_task

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentOut(BaseModel):
    id: str
    title: str
    source_type: str
    source_uri: str
    status: str
    error_message: str | None
    chunk_count: int
    size_bytes: int
    created_at: str
    indexed_at: str | None


def _to_out(d) -> DocumentOut:
    return DocumentOut(
        id=d.id,
        title=d.title,
        source_type=d.source_type,
        source_uri=d.source_uri,
        status=d.status,
        error_message=d.error_message,
        chunk_count=d.chunk_count,
        size_bytes=d.size_bytes,
        created_at=d.created_at.isoformat(),
        indexed_at=d.indexed_at.isoformat() if d.indexed_at else None,
    )


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    auth: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    settings = get_settings()
    service = DocumentService(session)
    filename = file.filename or "upload"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"unsupported file type: .{extension}, allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    raw_bytes = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"file exceeds {settings.max_upload_mb}MB limit")
    if not raw_bytes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="uploaded file is empty")

    document = await service.create_pending_upload(auth.tenant_id, filename, len(raw_bytes))

    try:
        ingest_document_task.delay(
            document_id=document.id,
            file_extension=extension,
            raw_bytes_b64=base64.b64encode(raw_bytes).decode("ascii"),
            title=filename,
            source_uri=document.source_uri,
            source_type="upload",
            connector_id=None,
        )
    except Exception as exc:
        await service.mark_queue_failed(document, f"failed to queue ingestion job: {exc}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ingestion queue is unavailable") from exc

    return _to_out(document)


@router.get("", response_model=list[DocumentOut])
async def list_documents(auth: AuthContext = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> list[DocumentOut]:
    service = DocumentService(session)
    documents = await service.list_documents(auth.tenant_id)
    return [_to_out(d) for d in documents]


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: str, auth: AuthContext = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> DocumentOut:
    service = DocumentService(session)
    try:
        document = await service.get_owned_document(document_id, auth.tenant_id)
    except AppError as exc:
        raise_http_from_app_error(exc)
    return _to_out(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str, auth: AuthContext = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> None:
    service = DocumentService(session)
    try:
        document = await service.get_owned_document(document_id, auth.tenant_id)
    except AppError as exc:
        raise_http_from_app_error(exc)
    await service.delete_document(auth.tenant_id, document)
