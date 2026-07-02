def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
    return scores


def weighted_fusion(score_maps: list[dict[str, float]], weights: list[float]) -> dict[str, float]:
    combined: dict[str, float] = {}
    for score_map, weight in zip(score_maps, weights, strict=True):
        if not score_map:
            continue
        max_score = max(score_map.values()) or 1.0
        for item_id, score in score_map.items():
            combined[item_id] = combined.get(item_id, 0.0) + weight * (score / max_score)
    return combined
