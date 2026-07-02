from fastapi import APIRouter

from app.api.v1 import analytics, auth, chat, connectors, documents, health, intelligence, models, reports, settings

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(documents.router)
api_router.include_router(connectors.router)
api_router.include_router(models.router)
api_router.include_router(analytics.router)
api_router.include_router(health.router)
api_router.include_router(intelligence.router)
api_router.include_router(reports.router)
api_router.include_router(settings.router)
