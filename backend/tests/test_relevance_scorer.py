from app.retrieval.relevance_scorer import combine_relevance_score, compute_confidence, mmr_select


def test_combine_relevance_score_higher_authority_increases_score():
    low_authority = combine_relevance_score(1.0, authority_weight=0.5, recency_boost=0.0)
    high_authority = combine_relevance_score(1.0, authority_weight=1.0, recency_boost=0.0)
    assert high_authority > low_authority


def test_compute_confidence_empty_scores_is_zero():
    assert compute_confidence([]) == 0.0


def test_compute_confidence_single_high_score():
    confidence = compute_confidence([0.95])
    assert 0.0 <= confidence <= 1.0
    assert confidence > 0.5


def test_compute_confidence_bounded_between_zero_and_one():
    confidence = compute_confidence([5.0, 0.0, 0.0])
    assert confidence <= 1.0


def test_mmr_select_returns_requested_count():
    candidates = [
        {"vector": [1.0, 0.0]},
        {"vector": [0.9, 0.1]},
        {"vector": [0.0, 1.0]},
    ]
    selected = mmr_select([1.0, 0.0], candidates, top_k=2)
    assert len(selected) == 2


def test_mmr_select_prefers_most_similar_first():
    candidates = [
        {"vector": [0.0, 1.0]},
        {"vector": [1.0, 0.0]},
    ]
    selected = mmr_select([1.0, 0.0], candidates, top_k=1)
    assert selected[0]["vector"] == [1.0, 0.0]


def test_mmr_select_empty_candidates():
    assert mmr_select([1.0, 0.0], [], top_k=3) == []
