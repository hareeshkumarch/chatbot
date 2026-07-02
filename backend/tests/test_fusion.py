from app.retrieval.fusion import reciprocal_rank_fusion, weighted_fusion


def test_reciprocal_rank_fusion_rewards_agreement_across_rankings():
    dense = ["a", "b", "c"]
    sparse = ["b", "a", "d"]
    scores = reciprocal_rank_fusion([dense, sparse])
    assert scores["a"] > scores["c"]
    assert scores["b"] > scores["d"]
    assert set(scores.keys()) == {"a", "b", "c", "d"}


def test_reciprocal_rank_fusion_single_ranking_preserves_order():
    scores = reciprocal_rank_fusion([["x", "y", "z"]])
    assert scores["x"] > scores["y"] > scores["z"]


def test_reciprocal_rank_fusion_empty_input():
    assert reciprocal_rank_fusion([]) == {}
    assert reciprocal_rank_fusion([[]]) == {}


def test_weighted_fusion_normalizes_by_max_score():
    dense_scores = {"a": 0.9, "b": 0.3}
    sparse_scores = {"a": 2.0, "c": 1.0}
    combined = weighted_fusion([dense_scores, sparse_scores], [0.7, 0.3])
    assert combined["a"] == 0.7 * 1.0 + 0.3 * 1.0
    assert combined["b"] == 0.7 * (0.3 / 0.9)
    assert combined["c"] == 0.3 * (1.0 / 2.0)


def test_weighted_fusion_skips_empty_score_maps():
    combined = weighted_fusion([{}, {"a": 1.0}], [0.5, 0.5])
    assert combined == {"a": 0.5}
