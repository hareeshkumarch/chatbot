from fastapi import HTTPException

from app.core.exceptions import AppError


def raise_http_from_app_error(exc: AppError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
