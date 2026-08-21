from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
from typing import Any

from app.db.session import get_db
from app.schemas.common import HealthStatus
from app.core.config import settings

router = APIRouter()

@router.get("/", response_model=HealthStatus)
async def health_check(db: AsyncSession = Depends(get_db)) -> Any:
    services_status = {}
    is_healthy = True
    is_degraded = False

    # Check Database
    try:
        await db.execute(text("SELECT 1"))
        services_status["database"] = "healthy"
    except Exception:
        services_status["database"] = "unhealthy"
        is_healthy = False

    # Check Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.aclose()
        services_status["redis"] = "healthy"
    except Exception:
        services_status["redis"] = "unhealthy"
        is_degraded = True

    if not is_healthy:
        overall_status = "unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    elif is_degraded:
        overall_status = "degraded"
        http_status = status.HTTP_200_OK
    else:
        overall_status = "healthy"
        http_status = status.HTTP_200_OK

    return JSONResponse(
        status_code=http_status,
        content={
            "status": overall_status,
            "version": "0.1.0",
            "services": services_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
