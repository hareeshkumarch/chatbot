from app.core.logging import get_logger
from app.llm.prompt_registry import render_prompt_with_user_message
from app.llm.router import TaskType, router
from app.orchestration.telemetry import record_llm_call

logger = get_logger(__name__)

UNVERIFIABLE_INTENTS = {"small_talk"}


def _parse_verification(content: str) -> tuple[bool, str | None]:
    text = content.strip()
    upper = text.upper()
    if upper.startswith("SUPPORTED"):
        return True, None
    reason = text.split("\n", 1)[-1].strip()
    if reason.upper().startswith("UNSUPPORTED"):
        reason = reason.split(" ", 1)[-1].strip() if " " in reason else None
    return False, reason or "answer contained unsupported claims"


async def check_grounding(
    answer: str,
    context_text: str,
    intent: str | None,
    explicit_provider: str | None = None,
    explicit_model: str | None = None,
    llm_calls: list[dict] | None = None,
) -> tuple[bool, list[dict], str | None]:
    llm_calls = llm_calls if llm_calls is not None else []
    if intent in UNVERIFIABLE_INTENTS or not context_text.strip():
        return True, llm_calls, None
    messages = render_prompt_with_user_message("verification", f"Answer:\n{answer}\n\nSource passages:\n{context_text}")
    try:
        response = await router.complete_with_fallback(
            TaskType.VERIFICATION,
            messages,
            explicit_provider=explicit_provider,
            explicit_model=explicit_model,
            max_tokens=120,
        )
    except Exception as exc:
        logger.warning(f"verification call failed, passing answer through unverified: {exc}")
        return True, llm_calls, None
    updated_calls = record_llm_call(
        llm_calls, "verification", response.provider, response.model, response.prompt_tokens, response.completion_tokens
    )
    verified, reason = _parse_verification(response.content)
    return verified, updated_calls, reason
