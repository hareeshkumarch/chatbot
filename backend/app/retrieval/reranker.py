import asyncio

from app.config import get_settings

_model = None


def _load_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder
        settings = get_settings()
        _model = CrossEncoder(settings.reranker_model, max_length=512)
    return _model


async def rerank(query: str, candidates: list[dict], top_k: int) -> list[dict]:
    settings = get_settings()
    if not settings.reranker_enabled or not candidates:
        return candidates[:top_k]
    loop = asyncio.get_event_loop()

    def _score():
        model = _load_model()
        pairs = [[query, c["payload"]["text"]] for c in candidates]
        return model.predict(pairs)

    scores = await loop.run_in_executor(None, _score)
    for candidate, score in zip(candidates, scores, strict=True):
        candidate["rerank_score"] = float(score)
    ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[:top_k]
