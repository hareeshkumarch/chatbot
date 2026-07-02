from langgraph.runtime import Runtime

from app.core.logging import get_logger
from app.core.node_tracing import traced_node
from app.llm.router import router
from app.orchestration.answer_formatting import build_synthesis_plan
from app.orchestration.state import GraphContext, GraphState
from app.orchestration.telemetry import record_llm_call

logger = get_logger(__name__)


@traced_node("synthesize")
async def synthesize_node(state: GraphState, runtime: Runtime[GraphContext]) -> GraphState:
    attempts = state.get("synthesis_attempts", 0)
    plan = build_synthesis_plan(state, retry=attempts > 0)

    if plan.skip_llm:
        return {
            **state,
            "answer": plan.fallback_answer,
            "citations": plan.citations,
            "verified": True,
            "synthesis_attempts": attempts + 1,
        }

    try:
        response = await router.complete_with_fallback(
            plan.task_type,
            plan.messages,
            explicit_provider=runtime.context.explicit_provider,
            explicit_model=runtime.context.explicit_model,
            max_tokens=plan.max_tokens,
        )
    except Exception as exc:
        logger.error(f"synthesis failed: {exc}")
        return {
            **state,
            "answer": "The answer could not be generated because all configured LLM providers are unavailable.",
            "citations": [],
            "verified": False,
            "synthesis_attempts": attempts + 1,
            "error": str(exc),
        }

    llm_calls = record_llm_call(
        state.get("llm_calls", []), "synthesis", response.provider, response.model, response.prompt_tokens, response.completion_tokens
    )

    return {
        **state,
        "answer": response.content,
        "citations": plan.citations,
        "provider_used": response.provider,
        "model_used": response.model,
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "synthesis_attempts": attempts + 1,
        "llm_calls": llm_calls,
    }
