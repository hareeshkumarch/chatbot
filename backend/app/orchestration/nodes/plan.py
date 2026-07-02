from app.core.logging import get_logger
from app.core.node_tracing import traced_node
from app.orchestration.planning import plan_query
from app.orchestration.state import GraphState

logger = get_logger(__name__)


@traced_node("plan")
async def plan_node(state: GraphState) -> GraphState:
    llm_calls = state.get("llm_calls", [])
    try:
        plan, llm_calls = await plan_query(state["query"], llm_calls)
    except Exception as exc:
        logger.warning(f"planning failed, defaulting to document_qa: {exc}")
        return {**state, "intent": "document_qa", "plan": [{"capability": "document_qa", "parameter": None}], "llm_calls": llm_calls}

    plan_dicts = [{"capability": s.capability, "parameter": s.parameter} for s in plan.steps]
    return {**state, "intent": plan.intent, "plan": plan_dicts, "llm_calls": llm_calls}


def route_after_plan(state: GraphState) -> str:
    if state.get("intent") == "small_talk":
        return "synthesize"
    return "execute_plan"
