import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from app.config import get_settings
from app.vectorstore.schema import ChunkPayload, collection_name

_client: AsyncQdrantClient | None = None


def get_qdrant() -> AsyncQdrantClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return _client


async def ensure_collection(tenant_id: str, vector_size: int) -> None:
    client = get_qdrant()
    name = collection_name(tenant_id)
    existing = await client.collection_exists(name)
    if existing:
        return
    await client.create_collection(
        collection_name=name,
        vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        sparse_vectors_config={"bm25": qmodels.SparseVectorParams()},
        hnsw_config=qmodels.HnswConfigDiff(ef_construct=200, m=16),
    )
    for field_name in ("document_id", "source_type", "connector_id"):
        await client.create_payload_index(name, field_name=field_name, field_schema=qmodels.PayloadSchemaType.KEYWORD)


async def upsert_chunks(tenant_id: str, vectors: list[list[float]], sparse_vectors: list[dict[int, float]], payloads: list[ChunkPayload]) -> list[str]:
    client = get_qdrant()
    name = collection_name(tenant_id)
    ids = [str(uuid.uuid4()) for _ in payloads]
    points = []
    for point_id, vector, sparse, payload in zip(ids, vectors, sparse_vectors, payloads, strict=True):
        sparse_vec = qmodels.SparseVector(indices=list(sparse.keys()), values=list(sparse.values())) if sparse else None
        vector_payload = {"": vector}
        if sparse_vec is not None:
            vector_payload["bm25"] = sparse_vec
        points.append(qmodels.PointStruct(id=point_id, vector=vector_payload, payload=payload.to_dict()))
    await client.upsert(collection_name=name, points=points)
    return ids


async def dense_search(tenant_id: str, query_vector: list[float], top_k: int, ef_search: int, filters: dict | None = None) -> list[dict]:
    client = get_qdrant()
    name = collection_name(tenant_id)
    query_filter = _build_filter(filters)
    results = await client.search(
        collection_name=name,
        query_vector=("", query_vector),
        limit=top_k,
        search_params=qmodels.SearchParams(hnsw_ef=ef_search),
        query_filter=query_filter,
        with_payload=True,
    )
    return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]


async def sparse_search(tenant_id: str, sparse_query: dict[int, float], top_k: int, filters: dict | None = None) -> list[dict]:
    client = get_qdrant()
    name = collection_name(tenant_id)
    query_filter = _build_filter(filters)
    sparse_vec = qmodels.SparseVector(indices=list(sparse_query.keys()), values=list(sparse_query.values()))
    results = await client.search(
        collection_name=name,
        query_vector=qmodels.NamedSparseVector(name="bm25", vector=sparse_vec),
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    )
    return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]


def _build_filter(filters: dict | None) -> qmodels.Filter | None:
    if not filters:
        return None
    conditions = [qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v)) for k, v in filters.items()]
    return qmodels.Filter(must=conditions)


async def count_points(tenant_id: str) -> int:
    client = get_qdrant()
    name = collection_name(tenant_id)
    if not await client.collection_exists(name):
        return 0
    result = await client.count(collection_name=name, exact=True)
    return result.count


async def delete_by_document(tenant_id: str, document_id: str) -> None:
    client = get_qdrant()
    name = collection_name(tenant_id)
    await client.delete(
        collection_name=name,
        points_selector=qmodels.FilterSelector(filter=qmodels.Filter(must=[qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id))])),
    )
