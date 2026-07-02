from dataclasses import dataclass, field

from app.llm.prompt_registry import render_prompt_with_user_message
from app.llm.router import TaskType, router
from app.orchestration.telemetry import record_llm_call

CAPABILITIES = {
    "document_qa", "sql_data", "connector_action",
    "web_search", "news", "places", "trends", "finance", "finance_history", "demographics",
}

MAX_PLAN_STEPS = 3


@dataclass
class PlanStep:
    capability: str
    parameter: str | None = None


@dataclass
class QueryPlan:
    intent: str
    steps: list[PlanStep] = field(default_factory=list)


def _parse_plan(raw: str) -> QueryPlan:
    cleaned = raw.strip()
    if cleaned.lower() == "small_talk":
        return QueryPlan(intent="small_talk", steps=[])

    steps: list[PlanStep] = []
    for chunk in cleaned.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" in chunk:
            capability, _, parameter = chunk.partition(":")
            capability = capability.strip().lower()
            parameter = parameter.strip() or None
        else:
            capability = chunk.strip().lower()
            parameter = None
        if capability in CAPABILITIES:
            steps.append(PlanStep(capability=capability, parameter=parameter))
        if len(steps) >= MAX_PLAN_STEPS:
            break

    if not steps:
        return QueryPlan(intent="document_qa", steps=[PlanStep(capability="document_qa", parameter=None)])

    intent = steps[0].capability if len(steps) == 1 else "multi"
    return QueryPlan(intent=intent, steps=steps)


async def plan_query(query: str, llm_calls: list[dict]) -> tuple[QueryPlan, list[dict]]:
    messages = render_prompt_with_user_message("query_classification", query)
    response = await router.complete_with_fallback(TaskType.QUERY_CLASSIFICATION, messages, max_tokens=100)
    updated_calls = record_llm_call(
        llm_calls, "query_planning", response.provider, response.model, response.prompt_tokens, response.completion_tokens
    )
    return _parse_plan(response.content), updated_calls
