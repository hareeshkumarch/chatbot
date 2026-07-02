from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import apply_runtime_overrides, get_settings, update_runtime_overrides
from app.core.api_key_fields import API_KEY_FIELDS
from app.dependencies import get_db
from app.services.platform_secrets import load_secrets, mask_secret, save_secrets

router = APIRouter(prefix="/settings", tags=["settings"])


class ApiKeyFieldOut(BaseModel):
    key: str
    label: str
    group: str
    secret: bool
    placeholder: str
    configured: bool
    masked_value: str | None = None


class ApiKeysOut(BaseModel):
    fields: list[ApiKeyFieldOut]


class UpdateApiKeysRequest(BaseModel):
    keys: dict[str, str | None] = Field(default_factory=dict)


@router.get("/api-keys", response_model=ApiKeysOut)
async def get_api_keys() -> ApiKeysOut:
    settings = get_settings()
    fields: list[ApiKeyFieldOut] = []
    for field in API_KEY_FIELDS:
        value = getattr(settings, field.key, None)
        configured = bool(value)
        fields.append(
            ApiKeyFieldOut(
                key=field.key,
                label=field.label,
                group=field.group,
                secret=field.secret,
                placeholder=field.placeholder,
                configured=configured,
                masked_value=mask_secret(value) if configured and field.secret and value else (value if configured and not field.secret else None),
            )
        )
    return ApiKeysOut(fields=fields)


@router.put("/api-keys", response_model=ApiKeysOut)
async def update_api_keys(payload: UpdateApiKeysRequest, session: AsyncSession = Depends(get_db)) -> ApiKeysOut:
    await save_secrets(session, payload.keys)
    update_runtime_overrides(payload.keys)
    return await get_api_keys()


async def bootstrap_platform_secrets(session: AsyncSession) -> None:
    secrets = await load_secrets(session)
    if secrets:
        apply_runtime_overrides(secrets)
