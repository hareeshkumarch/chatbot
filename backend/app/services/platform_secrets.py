from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_fields import MANAGED_SECRET_KEYS
from app.core.encryption import decrypt_payload, encrypt_payload
from app.db.models import PlatformSecret


def mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "••••••••"
    return f"{value[:4]}...{value[-4:]}"


async def load_secrets(session: AsyncSession) -> dict[str, str]:
    result = await session.execute(select(PlatformSecret))
    secrets: dict[str, str] = {}
    for row in result.scalars():
        if row.key in MANAGED_SECRET_KEYS:
            secrets[row.key] = decrypt_payload(row.encrypted_value)
    return secrets


async def save_secrets(session: AsyncSession, updates: dict[str, str | None]) -> dict[str, str]:
    stored: dict[str, str] = {}
    for key, value in updates.items():
        if key not in MANAGED_SECRET_KEYS:
            continue
        if value is None or value.strip() == "":
            existing = await session.get(PlatformSecret, key)
            if existing is not None:
                await session.delete(existing)
            continue
        trimmed = value.strip()
        existing = await session.get(PlatformSecret, key)
        if existing is None:
            session.add(PlatformSecret(key=key, encrypted_value=encrypt_payload(trimmed)))
        else:
            existing.encrypted_value = encrypt_payload(trimmed)
        stored[key] = trimmed
    await session.commit()
    return stored
