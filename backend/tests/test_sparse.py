from app.retrieval.sparse import _tokenize, to_sparse_vector


def test_tokenize_strips_stopwords_and_short_tokens():
    tokens = _tokenize("The quick brown fox is a fast animal")
    assert "the" not in tokens
    assert "is" not in tokens
    assert "a" not in tokens
    assert "quick" in tokens
    assert "fox" in tokens


def test_to_sparse_vector_empty_text_returns_empty_dict():
    assert to_sparse_vector("") == {}
    assert to_sparse_vector("the a an") == {}


def test_to_sparse_vector_is_deterministic():
    first = to_sparse_vector("agentic retrieval pipeline")
    second = to_sparse_vector("agentic retrieval pipeline")
    assert first == second


def test_to_sparse_vector_repeated_terms_score_higher():
    single = to_sparse_vector("retrieval pipeline")
    repeated = to_sparse_vector("retrieval retrieval retrieval pipeline")
    single_bucket = next(iter(single.keys()))
    assert repeated[single_bucket] > single[single_bucket]


def test_to_sparse_vector_bucket_range_is_bounded():
    from app.retrieval.sparse import VOCAB_BUCKETS

    vector = to_sparse_vector("enterprise agentic orchestration pipeline retrieval scoring")
    assert all(0 <= bucket < VOCAB_BUCKETS for bucket in vector)
