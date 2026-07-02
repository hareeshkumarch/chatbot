import math


def mmr_select(query_vector: list[float], candidates: list[dict], top_k: int, lambda_mult: float = 0.5) -> list[dict]:
    if not candidates:
        return []
    vectors = [c["vector"] for c in candidates]

    def norm(v: list[float]) -> list[float]:
        magnitude = math.sqrt(sum(x * x for x in v)) or 1e-8
        return [x / magnitude for x in v]

    def dot(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b, strict=True))

    q = norm(query_vector)
    normed = [norm(v) for v in vectors]
    sim_to_query = [dot(q, v) for v in normed]

    selected: list[int] = []
    remaining = list(range(len(candidates)))
    while remaining and len(selected) < top_k:
        if not selected:
            best = max(remaining, key=lambda i: sim_to_query[i])
        else:
            def mmr_score(i: int) -> float:
                diversity = max(dot(normed[i], normed[j]) for j in selected)
                return lambda_mult * sim_to_query[i] - (1 - lambda_mult) * diversity
            best = max(remaining, key=mmr_score)
        selected.append(best)
        remaining.remove(best)
    return [candidates[i] for i in selected]


def combine_relevance_score(base_score: float, authority_weight: float, recency_boost: float) -> float:
    return base_score * (0.7 + 0.2 * authority_weight + 0.1 * recency_boost)


def compute_confidence(top_scores: list[float]) -> float:
    if not top_scores:
        return 0.0
    top = top_scores[0]
    spread = 0.0
    if len(top_scores) > 1:
        spread = top - sum(top_scores[1:]) / len(top_scores[1:])
    confidence = min(1.0, max(0.0, top * 0.8 + max(0.0, spread) * 0.2))
    return confidence
