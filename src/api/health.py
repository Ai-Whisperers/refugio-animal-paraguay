"""Health check endpoint.

Returns application status and database connectivity. Used by load balancers
and monitoring systems to determine whether the instance is ready to serve traffic.
"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.error import COMMON_RESPONSES

router = APIRouter(tags=["health"], responses=COMMON_RESPONSES)

_DB_PING_QUERY = text("SELECT 1")


@router.get("/health")
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Check application and database health.

    Returns:
        200 {"status": "ok", "db": "connected"} when database is reachable.
        503 {"status": "degraded", "db": "unreachable"} when database is down.
    """
    try:
        await db.execute(_DB_PING_QUERY)
        return {"status": "ok", "db": "connected"}
    except Exception:  # degrade gracefully on any DB error; exception logged upstream
        response.status_code = 503
        return {"status": "degraded", "db": "unreachable"}
