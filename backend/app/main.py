import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.cache import get_redis
from app.api.v1.settings import bootstrap_platform_secrets
from app.core.default_identity import ensure_default_identity
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger, request_id_var
from app.core.metrics import render_metrics
from app.core.security import new_request_id
from app.core.tracing import configure_tracing
from app.db.base import async_session_maker, engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("starting enterprise ai platform backend")
    async with async_session_maker() as session:
        await bootstrap_platform_secrets(session)
        await ensure_default_identity(session)
    yield
    logger.info("shutting down enterprise ai platform backend")
    await engine.dispose()
    try:
        redis = get_redis()
        await redis.close()
    except Exception:
        pass


settings = get_settings()

app = FastAPI(title="Enterprise AI Platform", version="1.0.0", lifespan=lifespan)

configure_tracing(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = new_request_id()
    request_id_var.set(request_id)
    start = time.monotonic()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    except AppError as exc:
        logger.warning(f"app error on {request.method} {request.url.path}: {exc.message}")
        status_code = exc.status_code
        response = JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})
    except Exception as exc:
        logger.error(f"unhandled exception on {request.method} {request.url.path}: {exc}")
        response = JSONResponse(status_code=500, content={"code": "internal_error", "message": "an unexpected error occurred"})
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.info(f"request method={request.method} path={request.url.path} status={status_code} duration_ms={duration_ms}")
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    return response


@app.get("/health")
async def root_health() -> dict:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    data, content_type = render_metrics()
    return Response(content=data, media_type=content_type)


app.include_router(api_router, prefix=settings.api_prefix)
