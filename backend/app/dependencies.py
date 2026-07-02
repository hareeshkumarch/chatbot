from collections.abc import AsyncGenerator
from dataclasses import dataclass

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_redis
from app.core.default_identity import DEFAULT_ROLE, DEFAULT_TENANT_ID, DEFAULT_USER_EMAIL, DEFAULT_USER_ID
from app.core.logging import tenant_id_var
from app.core.security import decode_access_token
from app.db.session import get_session
from app.vectorstore.qdrant_client import get_qdrant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


@dataclass
class AuthContext:
    user_id: str
    tenant_id: str
    role: str
    email: str


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def get_current_user(token: str | None = Depends(oauth2_scheme)) -> AuthContext:
    if token:
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            if user_id and tenant_id:
                tenant_id_var.set(tenant_id)
                return AuthContext(user_id=user_id, tenant_id=tenant_id, role=payload.get("role", "member"), email=payload.get("email", ""))
        except jwt.InvalidTokenError:
            pass
    tenant_id_var.set(DEFAULT_TENANT_ID)
    return AuthContext(user_id=DEFAULT_USER_ID, tenant_id=DEFAULT_TENANT_ID, role=DEFAULT_ROLE, email=DEFAULT_USER_EMAIL)


async def get_current_tenant(auth: AuthContext = Depends(get_current_user)) -> str:
    return auth.tenant_id


def get_qdrant_client() -> AsyncQdrantClient:
    return get_qdrant()


def get_redis_client() -> Redis:
    return get_redis()
