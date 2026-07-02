from langgraph.runtime import Runtime

from app.core.node_tracing import traced_node
from app.orchestration.answer_formatting import format_plan_results
from app.orchestration.state import GraphContext, GraphState
from app.orchestration.verification import check_grounding

MAX_SYNTHESIS_ATTEMPTS = 2


@traced_node("verify")
async def verify_node(state: GraphState, runtime: Runtime[GraphContext]) -> GraphState:
    plan_results = state.get("plan_results") or []
    context_text, _, _ = format_plan_results(plan_results) if plan_results else ("", [], [])
    verified, llm_calls, _ = await check_grounding(
        state.get("answer", ""),
        context_text,
        state.get("intent"),
        runtime.context.explicit_provider,
        runtime.context.explicit_model,
        state.get("llm_calls", []),
    )
    return {**state, "verified": verified, "llm_calls": llm_calls}


def route_after_verify(state: GraphState) -> str:
    if state.get("verified", True):
        return "end"
    if state.get("synthesis_attempts", 0) >= MAX_SYNTHESIS_ATTEMPTS:
        return "end"
    return "retry"
