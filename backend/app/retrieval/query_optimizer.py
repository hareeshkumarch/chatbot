from app.llm.base import Message
from app.llm.prompt_registry import render_prompt_with_user_message
from app.llm.router import TaskType, router


async def rewrite_query(query: str, history: list[Message]) -> str:
    if not history:
        return query
    context = "\n".join(f"{m.role}: {m.content}" for m in history[-6:])
    messages = render_prompt_with_user_message("query_rewrite", f"History:\n{context}\n\nLatest question: {query}")
    response = await router.complete_with_fallback(TaskType.QUERY_REWRITE, messages, max_tokens=128)
    rewritten = response.content.strip()
    return rewritten if rewritten else query


async def generate_hyde_passage(query: str) -> str:
    messages = render_prompt_with_user_message("hyde", query)
    response = await router.complete_with_fallback(TaskType.HYDE, messages, max_tokens=180)
    return response.content.strip()
