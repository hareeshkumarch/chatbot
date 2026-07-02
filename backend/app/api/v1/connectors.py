import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.common import raise_http_from_app_error
from app.config import get_settings
from app.connectors.oauth import build_authorize_url, exchange_code, generate_state
from app.connectors.registry import CONNECTOR_CLASSES, OAUTH_CONNECTOR_TYPES
from app.core.cache import get_redis
from app.core.encryption import encrypt_payload
from app.core.exceptions import AppError
from app.core.limits import (
    CONNECTOR_NAME_MAX_LENGTH,
    CONNECTOR_TYPE_MAX_LENGTH,
    MAX_CONFIG_FIELDS,
    MAX_CREDENTIAL_FIELDS,
)
from app.core.logging import get_logger
from app.db.models import Connector, ConnectorCredential
from app.dependencies import AuthContext, get_current_user, get_db
from app.services.connector_service import REQUIRED_CONFIG_FIELDS, REQUIRED_CREDENTIAL_FIELDS, ConnectorService, auth_mode_for
from app.workers.tasks import sync_connector_task

logger = get_logger(__name__)

router = APIRouter(prefix="/connectors", tags=["connectors"])

OAUTH_STATE_TTL_SECONDS = 600


class ConnectorCreateRequest(BaseModel):
    type: str = Field(min_length=1, max_length=CONNECTOR_TYPE_MAX_LENGTH)
    name: str = Field(min_length=1, max_length=CONNECTOR_NAME_MAX_LENGTH)
    config: dict = Field(default_factory=dict)
    credentials: dict = Field(default_factory=dict)

    @field_validator("type", "name")
    @classmethod
    def _strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value cannot be empty or whitespace")
        return stripped

    @field_validator("config")
    @classmethod
    def _config_bounded(cls, value: dict) -> dict:
        if len(value) > MAX_CONFIG_FIELDS:
            raise ValueError(f"config cannot exceed {MAX_CONFIG_FIELDS} fields")
        return value

    @field_validator("credentials")
    @classmethod
    def _credentials_bounded(cls, value: dict) -> dict:
        if len(value) > MAX_CREDENTIAL_FIELDS:
            raise ValueError(f"credentials cannot exceed {MAX_CREDENTIAL_FIELDS} fields")
        return value


class ConnectorUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=CONNECTOR_NAME_MAX_LENGTH)
    config: dict | None = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be empty or whitespace")
        return stripped

    @field_validator("config")
    @classmethod
    def _config_bounded(cls, value: dict | None) -> dict | None:
        if value is not None and len(value) > MAX_CONFIG_FIELDS:
            raise ValueError(f"config cannot exceed {MAX_CONFIG_FIELDS} fields")
        return value


class ConnectorCredentialsUpdateRequest(BaseModel):
    credentials: dict

    @field_validator("credentials")
    @classmethod
    def _credentials_bounded(cls, value: dict) -> dict:
        if len(value) > MAX_CREDENTIAL_FIELDS:
            raise ValueError(f"credentials cannot exceed {MAX_CREDENTIAL_FIELDS} fields")
        return value


class ConnectorOut(BaseModel):
    id: str
    type: str
    name: str
    status: str
    config: dict
    last_synced_at: str | None
    created_at: str


class ConnectorTypeInfo(BaseModel):
    type: str
    auth_mode: str
    required_credential_fields: list[str]
    required_config_fields: list[str]


class AuthorizeUrlOut(BaseModel):
    authorize_url: str


class TestConnectionOut(BaseModel):
    connected: bool
    detail: str | None = None


def _to_out(c) -> ConnectorOut:
    return ConnectorOut(
        id=c.id,
        type=c.type,
        name=c.name,
        status=c.status,
        config=c.config,
        last_synced_at=c.last_synced_at.isoformat() if c.last_synced_at else None,
        created_at=c.created_at.isoformat(),
    )


@router.get("/types", response_model=list[ConnectorTypeInfo])
async def list_connector_types() -> list[ConnectorTypeInfo]:
    return [
        ConnectorTypeInfo(
            type=t,
            auth_mode=auth_mode_for(t),
            required_credential_fields=REQUIRED_CREDENTIAL_FIELDS.get(t, []),
            required_config_fields=REQUIRED_CONFIG_FIELDS.get(t, []),
        )
        for t in sorted(CONNECTOR_CLASSES.keys())
    ]


@router.get("", response_model=list[ConnectorOut])
async def list_connectors(auth: AuthContext = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> list[ConnectorOut]:
    service = ConnectorService(session)
    connectors = await service.list_connectors(auth.tenant_id)
    await service.refresh_active_gauge(auth.tenant_id, connectors)
    return [_to_out(c) for c in connectors]


@router.post("", response_model=ConnectorOut, status_code=status.HTTP_201_CREATED)
async def create_connector(
    payload: ConnectorCreateRequest, auth: AuthContext = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> ConnectorOut:
    service = ConnectorService(session)
    try:
        connector = await service.create_connector(auth.tenant_id, payload.type, payload.name, payload.config, payload.credentials)
    except AppError as exc:
        raise_http_from_app_error(exc)
    return _to_out(connector)


@router.patch("/{connector_id}", response_model=ConnectorOut)
async def update_connector(
    connector_id: str,
    payload: ConnectorUpdateRequest,
    auth: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ConnectorOut:
    service = ConnectorService(session)
    try:
        connector = await service.get_owned_connector(connector_id, auth.tenant_id)
        connector = await service.update_connector(connector, payload.name, payload.config)
    except AppError as exc:
        raise_http_from_app_error(exc)
    return _to_out(connector)


@router.put("/{connector_id}/credentials", response_model=ConnectorOut)
async def update_connector_credentials(
    connector_id: str,
    payload: ConnectorCredentialsUpdateRequest,
    auth: AuthContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ConnectorOut:
    service = ConnectorService(session)
    try:
        connector = await service.get_owned_connector(connector_id, auth.tenant_id)
        connector = await service.update_credentials(connector, payload.credentials)
    except AppError as exc:
        raise_http_from_app_error(exc)
    return _to_out(connector)


@router.get("/{connector_id}/authorize", response_model=AuthorizeUrlOut)
async def get_authorize_url(
    connector_id: str, auth: AuthContext = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> AuthorizeUrlOut:
    service = ConnectorService(session)
    try:
        connector = await service.get_owned_connector(connector_id, auth.tenant_id)
    except AppError as exc:
        raise_http_from_app_error(exc)
    if connector.type not in OAUTH_CONNECTOR_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="this connector type does not use OAuth")

    state = generate_state()
    redis = get_redis()
    await redis.set(f"oauth_state:{state}", connector_id, ex=OAUTH_STATE_TTL_SECONDS)
    return AuthorizeUrlOut(authorize_url=build_authorize_url(connector.type, state, connector.config))


@router.get("/{connector_type}/callback")
async def oauth_callback(connector_type: str, code: str, state: str, session: AsyncSession = Depends(get_db)) -> RedirectResponse:
    settings = get_settings()
    if connector_type not in OAUTH_CONNECTOR_TYPES:
        return RedirectResponse(f"{settings.frontend_url}/connectors?error=unsupported_type")

    redis = get_redis()
    state_key = f"oauth_state:{state}"
    connector_id = await redis.get(state_key)
    if not connector_id:
        return RedirectResponse(f"{settings.frontend_url}/connectors?error=invalid_or_expired_state")
    await redis.delete(state_key)

    result = await session.execute(select(Connector).where(Connector.id == connector_id))
    connector = result.scalar_one_or_none()
    if connector is None:
        return RedirectResponse(f"{settings.frontend_url}/connectors?error=connector_not_found")

    try:
        credentials = await exchange_code(connector_type, code, connector.config)
        if not credentials.get("access_token"):
            raise ValueError("token exchange did not return an access token")
    except Exception as exc:
        logger.error(f"oauth exchange failed for connector {connector_id}: {exc}")
        connector.status = "error"
        await session.commit()
        return RedirectResponse(f"{settings.frontend_url}/connectors?error=oauth_exchange_failed")

    existing = await session.execute(select(ConnectorCredential).where(ConnectorCredential.connector_id == connector.id))
    row = existing.scalar_one_or_none()
    encrypted = encrypt_payload(json.dumps(credentials))
    if row is None:
        session.add(ConnectorCredential(connector_id=connector.id, encrypted_payload=encrypted))
    else:
        row.encrypted_payload = encrypted
    connector.status = "connected"
    await session.commit()
    return RedirectResponse(f"{settings.frontend_url}/connectors?connected={connector_type}")


@router.post("/{connector_id}/test", response_model=TestConnectionOut)
async def test_connector(
    connector_id: str, auth: AuthContext = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> TestConnectionOut:
    service = ConnectorService(session)
    try:
        connector = await service.get_owned_connector(connector_id, auth.tenant_id)
    except AppError as exc:
        raise_http_from_app_error(exc)
    connected, detail = await service.test_connection(connector)
    return TestConnectionOut(connected=connected, detail=detail)


@router.post("/{connector_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_connector(
    connector_id: str, auth: AuthContext = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> dict:
    service = ConnectorService(session)
    try:
        connector = await service.get_owned_connector(connector_id, auth.tenant_id)
    except AppError as exc:
        raise_http_from_app_error(exc)
    if connector.status not in ("connected", "error"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"connector is not ready to sync (status={connector.status})")
    await service.mark_syncing(connector)
    try:
        sync_connector_task.delay(connector_id=connector_id)
    except Exception as exc:
        await service.mark_sync_failed(connector)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="sync queue is unavailable") from exc
    return {"queued": True, "connector_id": connector_id}


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(
    connector_id: str, auth: AuthContext = Depends(get_current_user), session: AsyncSession = Depends(get_db)
) -> None:
    service = ConnectorService(session)
    try:
        connector = await service.get_owned_connector(connector_id, auth.tenant_id)
    except AppError as exc:
        raise_http_from_app_error(exc)
    await service.delete_connector(auth.tenant_id, connector)
