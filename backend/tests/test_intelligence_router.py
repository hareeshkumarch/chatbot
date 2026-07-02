import pytest

from app.intelligence import router as intel_router
from app.intelligence.base import SearchResult


class FakeSearchProvider:
    def __init__(self, name: str, results: list[SearchResult] | None = None, should_raise: bool = False):
        self.name = name
        self._results = results or []
        self._should_raise = should_raise
        self.calls = 0

    async def search(self, query: str, max_results: int = 8, location: str | None = None) -> list[SearchResult]:
        self.calls += 1
        if self._should_raise:
            raise RuntimeError(f"{self.name} exploded")
        return self._results


@pytest.fixture
def sample_result():
    return SearchResult(title="Result", url="https://example.com", snippet="snippet", source="test")


async def test_web_search_uses_first_provider_with_results(monkeypatch, sample_result):
    tavily = FakeSearchProvider("tavily", [sample_result])
    exa = FakeSearchProvider("exa", [sample_result])
    monkeypatch.setattr(intel_router, "get_search_providers", lambda: {"tavily": tavily, "exa": exa})

    provider_name, results = await intel_router.run_web_search("query")

    assert provider_name == "tavily"
    assert len(results) == 1
    assert tavily.calls == 1
    assert exa.calls == 0


async def test_web_search_falls_back_when_first_provider_empty(monkeypatch, sample_result):
    tavily = FakeSearchProvider("tavily", [])
    exa = FakeSearchProvider("exa", [sample_result])
    monkeypatch.setattr(intel_router, "get_search_providers", lambda: {"tavily": tavily, "exa": exa})

    provider_name, _results = await intel_router.run_web_search("query")

    assert provider_name == "exa"
    assert tavily.calls == 1
    assert exa.calls == 1


async def test_web_search_falls_back_when_first_provider_raises(monkeypatch, sample_result):
    tavily = FakeSearchProvider("tavily", should_raise=True)
    serper = FakeSearchProvider("serper", [sample_result])
    monkeypatch.setattr(intel_router, "get_search_providers", lambda: {"tavily": tavily, "serper": serper})

    provider_name, results = await intel_router.run_web_search("query")

    assert provider_name == "serper"
    assert len(results) == 1


async def test_web_search_raises_when_all_providers_fail(monkeypatch):
    tavily = FakeSearchProvider("tavily", should_raise=True)
    monkeypatch.setattr(intel_router, "get_search_providers", lambda: {"tavily": tavily})

    with pytest.raises(RuntimeError):
        await intel_router.run_web_search("query")


async def test_web_search_returns_empty_when_nothing_configured(monkeypatch):
    monkeypatch.setattr(intel_router, "get_search_providers", lambda: {})

    provider_name, results = await intel_router.run_web_search("query")

    assert provider_name == ""
    assert results == []


async def test_web_search_respects_routing_priority_order(monkeypatch, sample_result):
    exa = FakeSearchProvider("exa", [sample_result])
    tavily = FakeSearchProvider("tavily", [sample_result])
    monkeypatch.setattr(intel_router, "get_search_providers", lambda: {"exa": exa, "tavily": tavily})

    provider_name, _ = await intel_router.run_web_search("query")

    assert provider_name == "tavily"


async def test_news_search_prefers_serper_over_fallback(monkeypatch, sample_result):
    class FakeSerper(FakeSearchProvider):
        async def search_news(self, query: str, max_results: int = 8, location: str | None = None) -> list[SearchResult]:
            self.calls += 1
            return self._results

    serper = FakeSerper("serper", [sample_result])
    monkeypatch.setattr(intel_router, "get_serper_provider", lambda: serper)

    provider_name, results = await intel_router.run_news_search("query")

    assert provider_name == "serper"
    assert len(results) == 1


async def test_news_search_falls_back_when_serper_not_configured(monkeypatch, sample_result):
    tavily = FakeSearchProvider("tavily", [sample_result])
    monkeypatch.setattr(intel_router, "get_serper_provider", lambda: None)
    monkeypatch.setattr(intel_router, "get_search_providers", lambda: {"tavily": tavily})

    provider_name, results = await intel_router.run_news_search("query")

    assert provider_name == "tavily"
    assert len(results) == 1
