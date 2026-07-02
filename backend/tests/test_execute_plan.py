from typing import ClassVar

from app.orchestration.nodes import execute_plan as execute_plan_module
from app.orchestration.nodes.execute_plan import execute_plan_node
from app.orchestration.steps import StepResult


class FakeContext:
    sql_connector = None
    active_connectors: ClassVar[list] = []
    explicit_provider = None
    explicit_model = None


class FakeRuntime:
    def __init__(self):
        self.context = FakeContext()


async def test_execute_plan_node_returns_empty_when_no_plan():
    state = {"query": "hi", "tenant_id": "t1"}
    result = await execute_plan_node(state, FakeRuntime())
    assert result["plan_results"] == []


async def test_execute_plan_node_dispatches_single_step(monkeypatch):
    async def fake_finance(symbol):
        return StepResult(capability="finance", parameter=symbol, data={"symbol": symbol, "price": 100.0})

    monkeypatch.setattr(execute_plan_module, "execute_finance_step", fake_finance)

    state = {"query": "tesla price", "tenant_id": "t1", "plan": [{"capability": "finance", "parameter": "TSLA"}], "llm_calls": []}
    result = await execute_plan_node(state, FakeRuntime())

    assert len(result["plan_results"]) == 1
    assert result["plan_results"][0]["data"]["symbol"] == "TSLA"
    assert result["llm_calls"] == []


async def test_execute_plan_node_runs_multiple_steps_and_preserves_order(monkeypatch):
    async def fake_finance(symbol):
        return StepResult(capability="finance", parameter=symbol, data={"symbol": symbol})

    async def fake_news(query):
        return StepResult(capability="news", parameter=query, data={"results": [{"title": "headline"}]})

    monkeypatch.setattr(execute_plan_module, "execute_finance_step", fake_finance)
    monkeypatch.setattr(execute_plan_module, "execute_news_step", fake_news)

    state = {
        "query": "tesla",
        "tenant_id": "t1",
        "plan": [{"capability": "finance", "parameter": "TSLA"}, {"capability": "news", "parameter": "Tesla"}],
        "llm_calls": [],
    }
    result = await execute_plan_node(state, FakeRuntime())

    assert len(result["plan_results"]) == 2
    assert result["plan_results"][0]["capability"] == "finance"
    assert result["plan_results"][1]["capability"] == "news"


async def test_execute_plan_node_merges_llm_calls_from_sql_step(monkeypatch):
    async def fake_sql_step(query, connector, explicit_provider, explicit_model, llm_calls):
        updated = [*llm_calls, {"task": "sql_generation", "provider": "anthropic", "model": "x", "prompt_tokens": 5, "completion_tokens": 3}]
        return StepResult(capability="sql_data", parameter=query, data={"rows": []}), updated

    monkeypatch.setattr(execute_plan_module, "execute_sql_step", fake_sql_step)

    state = {"query": "how many orders", "tenant_id": "t1", "plan": [{"capability": "sql_data", "parameter": None}], "llm_calls": []}
    result = await execute_plan_node(state, FakeRuntime())

    assert len(result["llm_calls"]) == 1
    assert result["llm_calls"][0]["task"] == "sql_generation"


async def test_execute_plan_node_preserves_pre_existing_llm_calls(monkeypatch):
    async def fake_finance(symbol):
        return StepResult(capability="finance", parameter=symbol, data={"symbol": symbol})

    monkeypatch.setattr(execute_plan_module, "execute_finance_step", fake_finance)

    existing_calls = [{"task": "query_planning", "provider": "groq", "model": "x", "prompt_tokens": 10, "completion_tokens": 2}]
    state = {"query": "tesla", "tenant_id": "t1", "plan": [{"capability": "finance", "parameter": "TSLA"}], "llm_calls": existing_calls}
    result = await execute_plan_node(state, FakeRuntime())

    assert result["llm_calls"] == existing_calls


async def test_execute_plan_node_falls_back_to_query_when_parameter_missing(monkeypatch):
    captured = {}

    async def fake_web_search(query):
        captured["query"] = query
        return StepResult(capability="web_search", parameter=query, data={"results": []})

    monkeypatch.setattr(execute_plan_module, "execute_web_search_step", fake_web_search)

    state = {"query": "who won the game", "tenant_id": "t1", "plan": [{"capability": "web_search", "parameter": None}], "llm_calls": []}
    await execute_plan_node(state, FakeRuntime())

    assert captured["query"] == "who won the game"


async def test_execute_plan_node_handles_unknown_capability_gracefully():
    state = {"query": "hi", "tenant_id": "t1", "plan": [{"capability": "not_a_real_one", "parameter": None}], "llm_calls": []}
    result = await execute_plan_node(state, FakeRuntime())
    assert result["plan_results"][0]["error"] is not None
