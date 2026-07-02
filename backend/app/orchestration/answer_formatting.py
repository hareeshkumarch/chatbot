import json
from dataclasses import dataclass, field

from app.llm.base import Message
from app.llm.prompt_registry import render_prompt_with_user_message
from app.llm.router import TaskType
from app.orchestration.state import GraphState
from app.orchestration.structured_content import extract_structured_blocks, format_rows_markdown

RETRY_INSTRUCTION = (
    "Your previous answer included claims not directly supported by the provided context. "
    "Answer again using only what the context explicitly states. "
    "If the context does not contain the answer, say so plainly instead of guessing."
)
NO_CONTEXT_ANSWER = "I could not find relevant information to answer this question."

LIVE_DATA_CAPABILITIES = {
    "sql_data",
    "connector_action",
    "finance",
    "finance_history",
    "trends",
    "demographics",
    "web_search",
    "news",
    "places",
}


@dataclass
class SynthesisPlan:
    task_type: TaskType
    messages: list[Message]
    citations: list[dict] = field(default_factory=list)
    blocks: list[dict] = field(default_factory=list)
    max_tokens: int = 800
    skip_llm: bool = False
    fallback_answer: str = ""


def format_plan_results(plan_results: list[dict]) -> tuple[str, list[dict], list[dict]]:
    blocks: list[str] = []
    citations: list[dict] = []
    counter = 0

    for result in plan_results:
        capability = result.get("capability")
        parameter = result.get("parameter")
        data = result.get("data") or {}
        error = result.get("error")
        label = f"{capability}" + (f" ({parameter})" if parameter else "")

        if error and not data:
            blocks.append(f"[{label}] could not be completed: {error}")
            continue

        if capability == "document_qa":
            chunks = data.get("chunks", [])
            if not chunks:
                blocks.append(f"[{label}] no relevant passages found in your documents")
                continue
            lines = []
            for chunk in chunks:
                counter += 1
                citations.append({
                    "index": counter,
                    "document_id": chunk.get("document_id"),
                    "title": chunk.get("title"),
                    "source_uri": chunk.get("source_uri"),
                    "page_number": chunk.get("page_number"),
                    "score": chunk.get("score"),
                })
                source = chunk.get("title") or chunk.get("source_uri") or "unknown source"
                lines.append(f"[{counter}] (source: {source})\n{chunk.get('text', '')}")
            blocks.append("Source: your documents\n" + "\n\n".join(lines))

        elif capability in ("web_search", "news", "places"):
            if "answer" in data:
                blocks.append(f"Source: {label}, already answered with citations\n{data['answer']}")
                for url in data.get("citations", []):
                    counter += 1
                    citations.append({"index": counter, "document_id": None, "title": None, "source_uri": url, "page_number": None, "score": None})
                continue
            results = data.get("results", [])
            if not results:
                blocks.append(f"[{label}] no results found")
                continue
            lines = []
            for item in results:
                counter += 1
                citations.append({
                    "index": counter,
                    "document_id": None,
                    "title": item.get("title"),
                    "source_uri": item.get("url"),
                    "page_number": None,
                    "score": None,
                })
                lines.append(f"[{counter}] {item.get('title', '')} \u2014 {item.get('snippet', '')}")
            blocks.append(f"Source: {label}\n" + "\n".join(lines))

        elif capability == "sql_data":
            rows = data.get("rows", [])
            if rows:
                blocks.append(f"Source: your database\n{format_rows_markdown(rows)}")
            else:
                blocks.append(f"[{label}] query returned no rows")

        elif capability == "connector_action":
            items = data.get("items", [])
            if items and isinstance(items, list) and items and isinstance(items[0], dict):
                blocks.append(f"Source: connected tools\n{format_rows_markdown(items, max_rows=30)}")
            else:
                blocks.append(f"Source: connected tools\n{json.dumps(items[:30], default=str)}")

        elif capability == "trends":
            points = data.get("points", [])
            if points:
                blocks.append(
                    f"Source: search trends for '{parameter}'\n"
                    f"{format_rows_markdown(points, max_rows=30)}"
                )
            else:
                blocks.append(f"Source: search trends for '{parameter}'\n{json.dumps(data, default=str)}")

        elif capability == "finance":
            blocks.append(f"Source: market data for {parameter}\n{json.dumps(data, default=str, indent=2)}")

        elif capability == "finance_history":
            points = data.get("points", [])
            symbol = data.get("symbol", parameter or "stock")
            period = data.get("period", "")
            if points:
                blocks.append(
                    f"Source: historical prices for {symbol} ({period})\n"
                    f"{format_rows_markdown(points, max_rows=30)}"
                )
            else:
                blocks.append(f"[{label}] no historical data available")

        elif capability == "demographics":
            blocks.append(f"Source: demographics for {parameter}\n{json.dumps(data, default=str, indent=2)}")

        else:
            blocks.append(f"Source: {label}\n{json.dumps(data, default=str)}")

    structured_blocks = extract_structured_blocks(plan_results)
    return "\n\n---\n\n".join(blocks), citations, structured_blocks


def _select_synthesis_prompt(plan_results: list[dict]) -> tuple[TaskType, str]:
    capabilities = {result.get("capability") for result in plan_results}
    has_document_qa = "document_qa" in capabilities
    has_live_data = bool(capabilities & LIVE_DATA_CAPABILITIES)
    if len(plan_results) > 1 or (has_document_qa and has_live_data):
        return TaskType.RETRIEVAL_SYNTHESIS, "multi_source_synthesis"
    if has_document_qa:
        return TaskType.RETRIEVAL_SYNTHESIS, "retrieval_synthesis"
    return TaskType.CONNECTOR_SYNTHESIS, "connector_synthesis"


def build_synthesis_plan(
    state: GraphState,
    retry: bool = False,
    retry_reason: str | None = None,
) -> SynthesisPlan:
    intent = state.get("intent", "document_qa")

    if intent == "small_talk":
        history = state.get("history", [])
        messages = render_prompt_with_user_message("general_chat", state["query"], history=history)
        return SynthesisPlan(task_type=TaskType.GENERAL_CHAT, messages=messages, max_tokens=400)

    plan_results = state.get("plan_results") or []

    if len(plan_results) == 1 and "answer" in (plan_results[0].get("data") or {}):
        data = plan_results[0]["data"]
        citation_urls = data.get("citations", [])
        citations = [
            {"index": i, "document_id": None, "title": None, "source_uri": url, "page_number": None, "score": None}
            for i, url in enumerate(citation_urls, start=1)
        ]
        return SynthesisPlan(
            task_type=TaskType.GENERAL_CHAT,
            messages=[],
            citations=citations,
            blocks=extract_structured_blocks(plan_results),
            max_tokens=0,
            skip_llm=True,
            fallback_answer=data["answer"],
        )

    if not plan_results:
        return SynthesisPlan(task_type=TaskType.RETRIEVAL_SYNTHESIS, messages=[], max_tokens=0, skip_llm=True, fallback_answer=NO_CONTEXT_ANSWER)

    all_failed = all(r.get("error") and not r.get("data") for r in plan_results)
    if all_failed:
        reasons = "; ".join(f"{r.get('capability')}: {r.get('error')}" for r in plan_results)
        return SynthesisPlan(
            task_type=TaskType.RETRIEVAL_SYNTHESIS,
            messages=[],
            max_tokens=0,
            skip_llm=True,
            fallback_answer=f"This needed live data that could not be retrieved: {reasons}",
        )

    context, citations, structured_blocks = format_plan_results(plan_results)
    content = f"Context:\n{context}\n\nQuestion: {state['query']}"
    if retry:
        content = f"{RETRY_INSTRUCTION}\n\n{content}"
        if retry_reason:
            content = f"Verification feedback: {retry_reason}\n\n{content}"

    task_type, prompt_key = _select_synthesis_prompt(plan_results)
    messages = render_prompt_with_user_message(prompt_key, content)

    return SynthesisPlan(
        task_type=task_type,
        messages=messages,
        citations=citations,
        blocks=structured_blocks,
        max_tokens=1000,
    )


def extract_confidence(plan_results: list[dict] | None) -> float | None:
    for result in plan_results or []:
        if result.get("capability") == "document_qa":
            return (result.get("data") or {}).get("confidence")
    return None


def extract_retrieval_strategy(plan_results: list[dict] | None) -> str:
    for result in plan_results or []:
        if result.get("capability") == "document_qa":
            return (result.get("data") or {}).get("strategy", "none")
    return "none"


def extract_document_chunk_count(plan_results: list[dict] | None) -> int:
    for result in plan_results or []:
        if result.get("capability") == "document_qa":
            return len((result.get("data") or {}).get("chunks", []))
    return 0


def extract_top_relevance_score(plan_results: list[dict] | None) -> float:
    for result in plan_results or []:
        if result.get("capability") == "document_qa":
            chunks = (result.get("data") or {}).get("chunks", [])
            return max((c.get("score", 0.0) for c in chunks), default=0.0)
    return 0.0
