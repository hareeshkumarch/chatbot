from dataclasses import dataclass

import pytest

from app.llm.router import router as llm_router
from app.orchestration import planning


@dataclass
class FakeResponse:
    content: str
    provider: str = "groq"
    model: str = "test-model"
    prompt_tokens: int = 10
    completion_tokens: int = 5


def _mock_response(monkeypatch, content: str) -> None:
    async def fake_complete_with_fallback(*args, **kwargs):
        return FakeResponse(content=content)

    monkeypatch.setattr(llm_router, "complete_with_fallback", fake_complete_with_fallback)


async def test_plan_query_single_plain_label(monkeypatch):
    _mock_response(monkeypatch, "document_qa")
    plan, calls = await planning.plan_query("what does the handbook say", [])
    assert plan.intent == "document_qa"
    assert len(plan.steps) == 1
    assert plan.steps[0].capability == "document_qa"
    assert plan.steps[0].parameter is None
    assert len(calls) == 1
    assert calls[0]["task"] == "query_planning"


async def test_plan_query_single_label_with_parameter(monkeypatch):
    _mock_response(monkeypatch, "finance:TSLA")
    plan, _ = await planning.plan_query("what's tesla trading at", [])
    assert plan.intent == "finance"
    assert plan.steps[0].capability == "finance"
    assert plan.steps[0].parameter == "TSLA"


async def test_plan_query_small_talk_has_no_steps(monkeypatch):
    _mock_response(monkeypatch, "small_talk")
    plan, _ = await planning.plan_query("hey how's it going", [])
    assert plan.intent == "small_talk"
    assert plan.steps == []


async def test_plan_query_multi_step_plan(monkeypatch):
    _mock_response(monkeypatch, "finance:TSLA;news:Tesla")
    plan, _ = await planning.plan_query("what's tesla's stock price and any recent news", [])
    assert plan.intent == "multi"
    assert len(plan.steps) == 2
    assert plan.steps[0].capability == "finance"
    assert plan.steps[0].parameter == "TSLA"
    assert plan.steps[1].capability == "news"
    assert plan.steps[1].parameter == "Tesla"


async def test_plan_query_strips_whitespace_and_case(monkeypatch):
    _mock_response(monkeypatch, "  Web_Search : bitcoin etf approval  ")
    plan, _ = await planning.plan_query("did the bitcoin etf get approved", [])
    assert plan.intent == "web_search"
    assert plan.steps[0].parameter == "bitcoin etf approval"


async def test_plan_query_invalid_steps_default_to_document_qa(monkeypatch):
    _mock_response(monkeypatch, "not_a_real_capability")
    plan, _ = await planning.plan_query("some question", [])
    assert plan.intent == "document_qa"
    assert plan.steps[0].capability == "document_qa"


async def test_plan_query_caps_step_count(monkeypatch):
    _mock_response(monkeypatch, "finance:AAPL;finance:MSFT;finance:GOOG;finance:AMZN")
    plan, _ = await planning.plan_query("compare these stocks", [])
    assert len(plan.steps) == planning.MAX_PLAN_STEPS


async def test_plan_query_appends_to_existing_llm_calls(monkeypatch):
    _mock_response(monkeypatch, "document_qa")
    existing_calls = [{"task": "previous", "provider": "openai", "model": "x", "prompt_tokens": 1, "completion_tokens": 1}]
    _, calls = await planning.plan_query("some question", existing_calls)
    assert len(calls) == 2
    assert calls[0]["task"] == "previous"
    assert calls[1]["task"] == "query_planning"


async def test_plan_query_propagates_provider_failure(monkeypatch):
    async def failing(*args, **kwargs):
        raise RuntimeError("all providers down")

    monkeypatch.setattr(llm_router, "complete_with_fallback", failing)
    with pytest.raises(RuntimeError):
        await planning.plan_query("some question", [])
