from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str
    image_base64: str | None = None
    image_media_type: str = "image/png"


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    raw: dict = field(default_factory=dict)


@dataclass
class StreamChunk:
    delta: str
    done: bool
    prompt_tokens: int = 0
    completion_tokens: int = 0
    provider: str | None = None
    model: str | None = None


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, messages: list[Message], model: str, temperature: float = 0.3, max_tokens: int = 1024) -> LLMResponse: ...

    @abstractmethod
    async def stream_complete(self, messages: list[Message], model: str, temperature: float = 0.3, max_tokens: int = 1024) -> AsyncIterator[StreamChunk]: ...


class EmbeddingProvider(ABC):
    name: str
    dimensions: int

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
