from dataclasses import dataclass

from app.config import get_settings


@dataclass
class RetrievalPlan:
    label: str
    dense_top_k: int
    sparse_top_k: int
    rerank_candidate_k: int
    final_top_k: int
    use_sparse: bool
    use_rerank: bool
    use_mmr: bool
    ef_search: int
    use_hyde: bool


def build_retrieval_plan(corpus_size: int) -> RetrievalPlan:
    settings = get_settings()
    if corpus_size <= 0:
        return RetrievalPlan("empty", 0, 0, 0, 0, False, False, False, 32, False)
    if corpus_size <= settings.small_corpus_threshold:
        capped = max(1, min(corpus_size, 200))
        return RetrievalPlan(
            label="small",
            dense_top_k=capped,
            sparse_top_k=capped,
            rerank_candidate_k=min(capped, 60),
            final_top_k=min(6, corpus_size),
            use_sparse=True,
            use_rerank=True,
            use_mmr=False,
            ef_search=64,
            use_hyde=False,
        )
    if corpus_size <= settings.large_corpus_threshold:
        return RetrievalPlan(
            label="medium",
            dense_top_k=50,
            sparse_top_k=50,
            rerank_candidate_k=30,
            final_top_k=8,
            use_sparse=True,
            use_rerank=True,
            use_mmr=True,
            ef_search=128,
            use_hyde=True,
        )
    return RetrievalPlan(
        label="large",
        dense_top_k=100,
        sparse_top_k=100,
        rerank_candidate_k=40,
        final_top_k=10,
        use_sparse=True,
        use_rerank=True,
        use_mmr=True,
        ef_search=256,
        use_hyde=True,
    )
