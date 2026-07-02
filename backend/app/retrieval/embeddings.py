import httpx

from app.config import get_settings
from app.llm.base import EmbeddingProvider


class OpenAIEmbedding(EmbeddingProvider):
    def __init__(self, api_key: str, base_url: str, model: str, dimensions: int):
        self.name = "openai"
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "input": texts}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.base_url}/embeddings", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        ordered = sorted(data["data"], key=lambda d: d["index"])
        return [item["embedding"] for item in ordered]


class GeminiEmbedding(EmbeddingProvider):
    def __init__(self, api_key: str, base_url: str, model: str, dimensions: int):
        self.name = "gemini"
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        results: list[list[float]] = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                payload = {"content": {"parts": [{"text": text}]}}
                resp = await client.post(f"{self.base_url}/models/{self.model}:embedContent", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                results.append(data["embedding"]["values"])
        return results


class LocalEmbedding(EmbeddingProvider):
    _model = None

    def __init__(self, model_name: str):
        self.name = "local"
        self.model_name = model_name
        self.dimensions = 384

    def _load(self):
        if LocalEmbedding._model is None:
            from sentence_transformers import SentenceTransformer
            LocalEmbedding._model = SentenceTransformer(self.model_name)
        return LocalEmbedding._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        model = self._load()
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(None, lambda: model.encode(texts, convert_to_numpy=True))
        return [v.tolist() for v in vectors]


_instance: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _instance
    if _instance is not None:
        return _instance
    settings = get_settings()
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        _instance = OpenAIEmbedding(settings.openai_api_key, settings.openai_base_url, settings.embedding_model, settings.embedding_dimensions)
    elif settings.embedding_provider == "gemini" and settings.gemini_api_key:
        _instance = GeminiEmbedding(settings.gemini_api_key, settings.gemini_base_url, "gemini-embedding-2", settings.embedding_dimensions)
    else:
        _instance = LocalEmbedding(settings.local_embedding_model)
    return _instance


def reset_embedding_provider() -> None:
    global _instance
    _instance = None
