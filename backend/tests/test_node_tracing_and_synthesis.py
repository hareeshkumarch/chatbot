import pytest

from app.core.node_tracing import traced_node
from app.orchestration.nodes.synthesize import synthesize_node


class FakeRuntime:
    def __init__(self, explicit_provider=None, explicit_model=None):
        self.context = self

    explicit_provider = None
    explicit_model = None


async def test_traced_node_passes_through_state_and_result():
    @traced_node("sample")
    async def sample_node(state):
        return {**state, "touched": True}

    result = await sample_node({"query": "hi"})
    assert result == {"query": "hi", "touched": True}


async def test_traced_node_reraises_exceptions():
    @traced_node("sample")
    async def failing_node(state):
        raise ValueError("boom")

    with pytest.raises(ValueError):
        await failing_node({"query": "hi"})


async def test_traced_node_works_with_extra_runtime_argument():
    @traced_node("sample")
    async def node_with_runtime(state, runtime):
        return {**state, "provider": runtime.context.explicit_provider}

    runtime = FakeRuntime()
    runtime.context.explicit_provider = "anthropic"
    result = await node_with_runtime({"query": "hi"}, runtime)
    assert result["provider"] == "anthropic"


async def test_synthesize_node_passes_through_citations_on_skip_llm():
    state = {
        "intent": "web_search",
        "query": "who won",
        "plan_results": [{"capability": "web_search", "parameter": "who won", "data": {"answer": "Team A won the match.", "citations": ["https://example.com/a", "https://example.com/b"]}}],
    }
    runtime = FakeRuntime()
    result = await synthesize_node(state, runtime)

    assert result["answer"] == "Team A won the match."
    assert result["verified"] is True
    assert len(result["citations"]) == 2
    assert result["citations"][0]["source_uri"] == "https://example.com/a"


async def test_synthesize_node_empty_citations_on_generic_fallback():
    state = {"intent": "document_qa", "query": "what does the handbook say", "plan_results": []}
    runtime = FakeRuntime()
    result = await synthesize_node(state, runtime)

    assert result["citations"] == []
    assert result["verified"] is True
