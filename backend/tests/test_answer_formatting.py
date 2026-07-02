from app.llm.router import TaskType
from app.orchestration.answer_formatting import (
    NO_CONTEXT_ANSWER,
    RETRY_INSTRUCTION,
    build_synthesis_plan,
    extract_confidence,
    extract_document_chunk_count,
    extract_retrieval_strategy,
    extract_top_relevance_score,
    format_plan_results,
)


def test_small_talk_routes_to_general_chat():
    state = {"intent": "small_talk", "query": "hello there", "history": []}
    plan = build_synthesis_plan(state)
    assert plan.task_type == TaskType.GENERAL_CHAT
    assert not plan.skip_llm
    assert plan.messages[-1].content == "hello there"


def test_no_plan_results_gives_generic_fallback():
    state = {"intent": "document_qa", "query": "what does the handbook say", "plan_results": []}
    plan = build_synthesis_plan(state)
    assert plan.skip_llm
    assert plan.fallback_answer == NO_CONTEXT_ANSWER


def test_single_document_qa_step_builds_citations():
    plan_results = [{
        "capability": "document_qa",
        "parameter": "revenue growth",
        "data": {
            "chunks": [{"document_id": "d1", "text": "revenue grew 20%", "title": "Q1 report", "source_uri": "s3://bucket/q1.pdf", "page_number": 2, "score": 0.9}],
            "confidence": 0.8,
            "strategy": "small",
        },
    }]
    state = {"intent": "document_qa", "query": "how did revenue grow", "plan_results": plan_results}
    plan = build_synthesis_plan(state)
    assert plan.task_type == TaskType.RETRIEVAL_SYNTHESIS
    assert len(plan.citations) == 1
    assert plan.citations[0]["document_id"] == "d1"
    assert "revenue grew 20%" in plan.messages[-1].content


def test_all_steps_failed_gives_specific_fallback():
    plan_results = [
        {"capability": "finance", "parameter": "TSLA", "data": {}, "error": "could not retrieve a quote for TSLA"},
        {"capability": "news", "parameter": "Tesla", "data": {}, "error": "no news providers are configured"},
    ]
    state = {"intent": "multi", "query": "tesla stock and news", "plan_results": plan_results}
    plan = build_synthesis_plan(state)
    assert plan.skip_llm
    assert "could not be retrieved" in plan.fallback_answer
    assert "TSLA" in plan.fallback_answer


def test_multi_step_plan_combines_sources_into_one_synthesis_call():
    plan_results = [
        {"capability": "finance", "parameter": "TSLA", "data": {"symbol": "TSLA", "price": 245.3, "currency": "USD", "change_percent": 2.1}},
        {"capability": "news", "parameter": "Tesla", "data": {"results": [{"title": "Tesla news", "url": "https://example.com/a", "snippet": "something happened"}], "provider": "serper"}},
    ]
    state = {"intent": "multi", "query": "tesla stock and news", "plan_results": plan_results}
    plan = build_synthesis_plan(state)
    assert plan.task_type == TaskType.CONNECTOR_SYNTHESIS
    assert not plan.skip_llm
    assert len(plan.citations) == 1
    content = plan.messages[-1].content
    assert "TSLA" in content
    assert "Tesla news" in content


def test_web_search_direct_answer_skips_llm_entirely():
    plan_results = [{"capability": "web_search", "parameter": "who won", "data": {"answer": "Team A won.", "citations": ["https://example.com/a", "https://example.com/b"]}}]
    state = {"intent": "web_search", "query": "who won", "plan_results": plan_results}
    plan = build_synthesis_plan(state)
    assert plan.skip_llm
    assert plan.fallback_answer == "Team A won."
    assert len(plan.citations) == 2


def test_retry_adds_stricter_instruction_to_prompt():
    plan_results = [{"capability": "document_qa", "parameter": "x", "data": {"chunks": [{"document_id": "d1", "text": "revenue grew 20%", "title": "Q1", "source_uri": "s3://x", "page_number": None, "score": 0.5}], "confidence": 0.5, "strategy": "small"}}]
    state = {"intent": "document_qa", "query": "how did revenue grow", "plan_results": plan_results}
    plan = build_synthesis_plan(state, retry=True)
    assert RETRY_INSTRUCTION in plan.messages[-1].content


def test_multi_step_plan_uses_multi_source_prompt():
    plan_results = [
        {"capability": "document_qa", "parameter": "handbook", "data": {"chunks": [{"document_id": "d1", "text": "remote work allowed", "title": "Handbook", "source_uri": "s3://x", "page_number": 1, "score": 0.8}], "confidence": 0.8, "strategy": "small"}},
        {"capability": "finance", "parameter": "TSLA", "data": {"symbol": "TSLA", "price": 245.3}},
    ]
    state = {"intent": "multi", "query": "remote work policy and tsla price", "plan_results": plan_results}
    plan = build_synthesis_plan(state)
    assert plan.task_type == TaskType.RETRIEVAL_SYNTHESIS
    assert "synthesizing every source" in plan.messages[0].content.lower()
    assert len(plan.blocks) >= 1


def test_format_plan_results_labels_each_source():
    plan_results = [
        {"capability": "sql_data", "parameter": None, "data": {"rows": [{"count": 5}]}},
        {"capability": "trends", "parameter": "bitcoin", "data": {"keyword": "bitcoin", "points": [{"date": "2026-01-01", "value": 50}], "related_queries": []}},
    ]
    context, citations, blocks = format_plan_results(plan_results)
    assert "your database" in context
    assert "bitcoin" in context
    assert citations == []
    assert "| count |" in context or "count" in context
    assert len(blocks) >= 1


def test_extract_confidence_reads_document_qa_step():
    plan_results = [{"capability": "finance", "parameter": "TSLA", "data": {}}, {"capability": "document_qa", "parameter": "x", "data": {"confidence": 0.73, "chunks": [], "strategy": "small"}}]
    assert extract_confidence(plan_results) == 0.73


def test_extract_confidence_none_when_no_document_qa_step():
    plan_results = [{"capability": "finance", "parameter": "TSLA", "data": {}}]
    assert extract_confidence(plan_results) is None


def test_extract_retrieval_strategy_defaults_to_none():
    assert extract_retrieval_strategy([]) == "none"
    assert extract_retrieval_strategy([{"capability": "finance", "parameter": "TSLA", "data": {}}]) == "none"


def test_extract_document_chunk_count_and_top_score():
    plan_results = [{
        "capability": "document_qa", "parameter": "x",
        "data": {"chunks": [{"score": 0.4}, {"score": 0.9}], "confidence": 0.5, "strategy": "small"},
    }]
    assert extract_document_chunk_count(plan_results) == 2
    assert extract_top_relevance_score(plan_results) == 0.9
