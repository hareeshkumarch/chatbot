import functools
import time
from collections.abc import Awaitable, Callable

from app.core.logging import get_logger, request_id_var, tenant_id_var
from app.core.phoenix_tracing import trace_orchestration_node

logger = get_logger("orchestration.trace")


def traced_node(node_name: str) -> Callable[[Callable[..., Awaitable]], Callable[..., Awaitable]]:
    def decorator(func: Callable[..., Awaitable]) -> Callable[..., Awaitable]:
        @functools.wraps(func)
        async def wrapper(state, *args, **kwargs):
            intent = state.get("intent") if isinstance(state, dict) else None
            start = time.monotonic()
            async with trace_orchestration_node(node_name, intent=intent):
                try:
                    result = await func(state, *args, **kwargs)
                except Exception as exc:
                    duration_ms = int((time.monotonic() - start) * 1000)
                    logger.error(
                        f"node_error node={node_name} duration_ms={duration_ms} error={exc} "
                        f"request_id={request_id_var.get()} tenant_id={tenant_id_var.get()}"
                    )
                    raise
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.debug(f"node_done node={node_name} duration_ms={duration_ms}")
            return result

        return wrapper

    return decorator
