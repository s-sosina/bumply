from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.session import get_db

router = APIRouter()


@router.get("/health")
def health_check():
    """Liveness: is the process up at all? Checks no dependencies."""
    return {"status": "ok", "service": "Bumply"}


@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    """Readiness (core): without Postgres the app cannot serve real requests -> 503."""
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"db": "down"})
    return {"db": "ok"}


@router.get("/health/redis")
async def health_redis(redis: Redis = Depends(get_redis)):
    """Readiness (supporting): Redis is a cache layer, so an outage is 'degraded', not fatal."""
    try:
        await redis.ping()
    except Exception:
        return {"redis": "down"}
    return {"redis": "ok"}
