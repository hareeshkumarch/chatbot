import pytest

from app.core.exceptions import ProviderUnavailableError
from app.llm import router as router_module
from app.llm.router import ModelRouter, TaskType


@pytest.fixture
def configured_providers(monkeypatch):
    monkeypatch.setattr(router_module, "available_providers", lambda: ["groq", "anthropic", "openai"])
    monkeypatch.setattr(
        router_module,
        "DEFAULT_MODELS",
        {"groq": "openai/gpt-oss-120b", "anthropic": "claude-sonnet-5", "openai": "gpt-5.5"},
    )


def test_resolve_uses_task_routing_table_order(configured_providers):
    router = ModelRouter()
    decision = router.resolve(TaskType.QUERY_CLASSIFICATION)
    assert decision.provider == "groq"
    assert decision.model == "openai/gpt-oss-120b"
    assert decision.fallback_chain[0] == "groq"


def test_resolve_filters_unconfigured_providers_from_chain(configured_providers):
    router = ModelRouter()
    decision = router.resolve(TaskType.RETRIEVAL_SYNTHESIS)
    assert "grok" not in decision.fallback_chain
    assert "moonshot" not in decision.fallback_chain
    assert set(decision.fallback_chain) == {"groq", "anthropic", "openai"}


def test_resolve_explicit_provider_takes_priority(configured_providers):
    router = ModelRouter()
    decision = router.resolve(TaskType.QUERY_CLASSIFICATION, explicit_provider="anthropic")
    assert decision.provider == "anthropic"
    assert decision.fallback_chain[0] == "anthropic"
    assert decision.model == "claude-sonnet-5"


def test_resolve_explicit_provider_and_model_override(configured_providers):
    router = ModelRouter()
    decision = router.resolve(TaskType.GENERAL_CHAT, explicit_provider="openai", explicit_model="gpt-5.5-mini")
    assert decision.model == "gpt-5.5-mini"


def test_resolve_rejects_unconfigured_explicit_provider(configured_providers):
    router = ModelRouter()
    with pytest.raises(ProviderUnavailableError):
        router.resolve(TaskType.GENERAL_CHAT, explicit_provider="grok")


def test_resolve_raises_when_nothing_is_configured(monkeypatch):
    monkeypatch.setattr(router_module, "available_providers", lambda: [])
    router = ModelRouter()
    with pytest.raises(ProviderUnavailableError):
        router.resolve(TaskType.GENERAL_CHAT)
