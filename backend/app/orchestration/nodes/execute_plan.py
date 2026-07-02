import asyncio

from langgraph.runtime import Runtime

from app.core.logging import get_logger
from app.core.node_tracing import traced_node
from app.orchestration.state import GraphContext, GraphState
from app.orchestration.steps import (
    StepResult,
    execute_connector_step,
    execute_demographics_step,
    execute_document_qa_step,
    execute_finance_step,
    execute_news_step,
    execute_places_step,
    execute_sql_step,
    execute_trends_step,
    execute_web_search_step,
)

logger = get_logger(__name__)


async def _run_step(step: dict, state: GraphState, runtime: Runtime[GraphContext], llm_calls: list[dict]) -> tuple[StepResult, list[dict]]:
    capability = step.get("capability")
    parameter = step.get("parameter") or state["query"]

    if capability == "document_qa":
        return await execute_document_qa_step(parameter, state["tenant_id"], state.get("history", [])), llm_calls
    if capability == "sql_data":
        return await execute_sql_step(
            parameter, runtime.context.sql_connector, runtime.context.explicit_provider, runtime.context.explicit_model, llm_calls
        )
    if capability == "connector_action":
        return await execute_connector_step(parameter, runtime.context.active_connectors), llm_calls
    if capability == "web_search":
        return await execute_web_search_step(parameter), llm_calls
    if capability == "news":
        return await execute_news_step(parameter), llm_calls
    if capability == "places":
        return await execute_places_step(parameter), llm_calls
    if capability == "trends":
        return await execute_trends_step(parameter), llm_calls
    if capability == "finance":
        return await execute_finance_step(parameter), llm_calls
    if capability == "demographics":
        return await execute_demographics_step(parameter), llm_calls
    return StepResult(capability=str(capability), parameter=parameter, error=f"unhandled capability: {capability}"), llm_calls


@traced_node("execute_plan")
async def execute_plan_node(state: GraphState, runtime: Runtime[GraphContext]) -> GraphState:
    plan = state.get("plan") or []
    if not plan:
        return {**state, "plan_results": []}

    base_calls = state.get("llm_calls", [])
    outcomes = await asyncio.gather(*(_run_step(step, state, runtime, base_calls) for step in plan))

    plan_results = []
    llm_calls = list(base_calls)
    for step_result, updated_calls in outcomes:
        plan_results.append(step_result.__dict__)
        llm_calls.extend(updated_calls[len(base_calls):])

    return {**state, "plan_results": plan_results, "llm_calls": llm_calls}
