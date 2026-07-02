import hashlib
import math
import re

VOCAB_BUCKETS = 30000
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "and", "or",
    "but", "if", "then", "else", "of", "to", "in", "on", "for", "with", "as", "by",
    "at", "from", "this", "that", "these", "those", "it", "its", "into", "about",
}


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def _bucket(term: str) -> int:
    digest = hashlib.md5(term.encode("utf-8")).hexdigest()
    return int(digest, 16) % VOCAB_BUCKETS


def to_sparse_vector(text: str) -> dict[int, float]:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    counts: dict[int, int] = {}
    for token in tokens:
        bucket = _bucket(token)
        counts[bucket] = counts.get(bucket, 0) + 1
    return {bucket: 1.0 + math.log(count) for bucket, count in counts.items()}
