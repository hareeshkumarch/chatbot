import hashlib
import json
import math

from redis.asyncio import Redis

from app.config import get_settings

_client: Redis | None = None


def get_redis() -> Redis:
    global _client
    if _client is None:
        settings = get_settings()
        _client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def _hash_key(tenant_id: str, query: str) -> str:
    raw = f"{tenant_id}:{query.strip().lower()}"
    return "cache:exact:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def get_exact_cache(tenant_id: str, query: str) -> dict | None:
    redis = get_redis()
    raw = await redis.get(_hash_key(tenant_id, query))
    if raw is None:
        return None
    return json.loads(raw)


async def set_exact_cache(tenant_id: str, query: str, payload: dict) -> None:
    settings = get_settings()
    redis = get_redis()
    await redis.set(_hash_key(tenant_id, query), json.dumps(payload), ex=settings.semantic_cache_ttl_seconds)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def get_semantic_cache(tenant_id: str, query_vector: list[float]) -> dict | None:
    settings = get_settings()
    redis = get_redis()
    index_key = f"cache:semantic_index:{tenant_id}"
    entries = await redis.lrange(index_key, 0, 200)
    best_score = 0.0
    best_payload = None
    for entry_key in entries:
        raw = await redis.get(entry_key)
        if raw is None:
            continue
        entry = json.loads(raw)
        score = _cosine(query_vector, entry["vector"])
        if score > best_score:
            best_score = score
            best_payload = entry["payload"]
    if best_score >= settings.semantic_cache_similarity_threshold:
        return best_payload
    return None


async def set_semantic_cache(tenant_id: str, query_vector: list[float], payload: dict) -> None:
    settings = get_settings()
    redis = get_redis()
    index_key = f"cache:semantic_index:{tenant_id}"
    entry_key = f"cache:semantic_entry:{tenant_id}:{hashlib.sha256(json.dumps(query_vector).encode()).hexdigest()[:16]}"
    await redis.set(entry_key, json.dumps({"vector": query_vector, "payload": payload}), ex=settings.semantic_cache_ttl_seconds)
    await redis.lpush(index_key, entry_key)
    await redis.ltrim(index_key, 0, 200)
    await redis.expire(index_key, settings.semantic_cache_ttl_seconds)
