from celery import Celery
from celery.signals import worker_process_init

from app.config import apply_runtime_overrides, get_settings

settings = get_settings()

celery_app = Celery("enterprise_ai_platform", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)

celery_app.autodiscover_tasks(["app.workers"])


@worker_process_init.connect
def load_worker_secrets(**kwargs) -> None:
    import asyncio

    from app.db.base import async_session_maker
    from app.services.platform_secrets import load_secrets

    async def _load() -> dict[str, str]:
        async with async_session_maker() as session:
            return await load_secrets(session)

    secrets = asyncio.run(_load())
    if secrets:
        apply_runtime_overrides(secrets)
