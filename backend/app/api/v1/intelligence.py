from fastapi import APIRouter
from pydantic import BaseModel

from app.intelligence.router import available_intelligence_capabilities

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class CapabilitiesOut(BaseModel):
    web_search: list[str]
    direct_answer: list[str]
    news: list[str]
    places: list[str]
    trends: list[str]
    finance: list[str]
    demographics: list[str]


@router.get("/capabilities", response_model=CapabilitiesOut)
async def get_capabilities() -> CapabilitiesOut:
    return CapabilitiesOut(**available_intelligence_capabilities())
