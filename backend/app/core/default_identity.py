import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.models import Tenant, User

logger = get_logger(__name__)

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000002"
DEFAULT_TENANT_NAME = "Default Workspace"
DEFAULT_USER_EMAIL = "workspace@local"
DEFAULT_ROLE = "admin"


async def ensure_default_identity(session: AsyncSession) -> None:
    tenant_result = await session.execute(select(Tenant).where(Tenant.id == DEFAULT_TENANT_ID))
    if tenant_result.scalar_one_or_none() is None:
        session.add(Tenant(id=DEFAULT_TENANT_ID, name=DEFAULT_TENANT_NAME, plan="default"))
        logger.info(f"created default tenant {DEFAULT_TENANT_ID}")

    user_result = await session.execute(select(User).where(User.id == DEFAULT_USER_ID))
    if user_result.scalar_one_or_none() is None:
        session.add(
            User(
                id=DEFAULT_USER_ID,
                tenant_id=DEFAULT_TENANT_ID,
                email=DEFAULT_USER_EMAIL,
                hashed_password=hash_password(secrets.token_urlsafe(32)),
                role=DEFAULT_ROLE,
            )
        )
        logger.info(f"created default user {DEFAULT_USER_ID}")

    await session.commit()
