import time
from dataclasses import dataclass

from app.core.cache import get_exact_cache, set_exact_cache
from app.core.logging import get_logger
from app.core.metrics import retrieval_hit_count, retrieval_latency_seconds
from app.llm.base import Message
from app.retrieval.adaptive_strategy import build_retrieval_plan
from app.retrieval.embeddings import get_embedding_provider
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.query_optimizer import generate_hyde_passage, rewrite_query
from app.retrieval.relevance_scorer import combine_relevance_score, compute_confidence, mmr_select
from app.retrieval.reranker import rerank
from app.retrieval.sparse import to_sparse_vector
from app.vectorstore.qdrant_client import count_points, dense_search, sparse_search

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    document_id: str
    text: str
    title: str
    source_uri: str
    source_type: str
    score: float
    page_number: int | None = None


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    strategy: str
    confidence: float
    from_cache: bool = False
    query_used: str = ""


async def run_retrieval(tenant_id: str, query: str, history: list[Message] | None = None) -> RetrievalResult:
    start = time.monotonic()
    history = history or []

    cached = await get_exact_cache(tenant_id, query)
    if cached:
        chunks = [RetrievedChunk(**c) for c in cached["chunks"]]
        return RetrievalResult(chunks=chunks, strategy=cached["strategy"], confidence=cached["confidence"], from_cache=True, query_used=query)

    corpus_size = await count_points(tenant_id)
    plan = build_retrieval_plan(corpus_size)
    if plan.label == "empty":
        return RetrievalResult(chunks=[], strategy="empty", confidence=0.0, query_used=query)

    search_query = await rewrite_query(query, history)
    embed_target = search_query
    if plan.use_hyde:
        hyde_passage = await generate_hyde_passage(search_query)
        if hyde_passage:
            embed_target = hyde_passage

    embedder = get_embedding_provider()
    query_vector = (await embedder.embed([embed_target]))[0]
    sparse_query = to_sparse_vector(search_query)

    dense_results = await dense_search(tenant_id, query_vector, plan.dense_top_k, plan.ef_search)
    sparse_results = await sparse_search(tenant_id, sparse_query, plan.sparse_top_k) if plan.use_sparse and sparse_query else []

    by_id = {r["id"]: r for r in dense_results}
    for r in sparse_results:
        by_id.setdefault(r["id"], r)

    dense_ranking = [r["id"] for r in dense_results]
    sparse_ranking = [r["id"] for r in sparse_results]
    fused_scores = reciprocal_rank_fusion([dense_ranking, sparse_ranking]) if sparse_ranking else {r["id"]: r["score"] for r in dense_results}

    candidates = []
    for point_id, fused_score in sorted(fused_scores.items(), key=lambda kv: kv[1], reverse=True)[: plan.rerank_candidate_k]:
        record = by_id[point_id]
        candidates.append({
            "id": point_id,
            "vector": query_vector,
            "fused_score": fused_score,
            "payload": record["payload"],
        })

    if plan.use_rerank:
        candidates = await rerank(search_query, candidates, plan.rerank_candidate_k)
        score_key = "rerank_score"
    else:
        score_key = "fused_score"

    candidates = mmr_select(query_vector, candidates, plan.final_top_k) if plan.use_mmr else candidates[: plan.final_top_k]

    chunks: list[RetrievedChunk] = []
    top_scores: list[float] = []
    for c in candidates:
        payload = c["payload"]
        raw_score = float(c.get(score_key, c.get("fused_score", 0.0)))
        adjusted = combine_relevance_score(raw_score, payload.get("authority_weight", 1.0), 0.0)
        top_scores.append(adjusted)
        chunks.append(RetrievedChunk(
            document_id=payload["document_id"],
            text=payload["text"],
            title=payload["title"],
            source_uri=payload["source_uri"],
            source_type=payload["source_type"],
            score=adjusted,
            page_number=payload.get("page_number"),
        ))

    confidence = compute_confidence(sorted(top_scores, reverse=True))
    latency = time.monotonic() - start
    retrieval_latency_seconds.labels(strategy=plan.label).observe(latency)
    retrieval_hit_count.labels(strategy=plan.label).observe(len(chunks))

    result = RetrievalResult(chunks=chunks, strategy=plan.label, confidence=confidence, query_used=search_query)

    if chunks:
        await set_exact_cache(tenant_id, query, {
            "chunks": [c.__dict__ for c in chunks],
            "strategy": plan.label,
            "confidence": confidence,
        })

    return result
