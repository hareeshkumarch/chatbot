from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.cache import get_redis
from app.db.base import async_session_maker
from app.llm.registry import available_providers
from app.vectorstore.qdrant_client import get_qdrant

router = APIRouter(prefix="/health", tags=["health"])


class ReadinessOut(BaseModel):
    status: str
    database: bool
    redis: bool
    qdrant: bool
    configured_llm_providers: list[str]


@router.get("")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready", response_model=ReadinessOut)
async def readiness() -> ReadinessOut:
    db_ok = False
    redis_ok = False
    qdrant_ok = False

    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        redis = get_redis()
        await redis.ping()
        redis_ok = True
    except Exception:
        pass

    try:
        client = get_qdrant()
        await client.get_collections()
        qdrant_ok = True
    except Exception:
        pass

    overall = "ok" if (db_ok and redis_ok and qdrant_ok) else "degraded"
    return ReadinessOut(
        status=overall,
        database=db_ok,
        redis=redis_ok,
        qdrant=qdrant_ok,
        configured_llm_providers=available_providers(),
    )
