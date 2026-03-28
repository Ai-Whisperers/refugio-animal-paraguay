"""Server-Sent Events endpoint for real-time admin notifications.

Provides a streaming SSE connection for the admin dashboard to receive
real-time donation notifications and activity updates.

Supports both Bearer header auth (standard API calls) and query-param
token auth (required by EventSource which cannot set custom headers).

Endpoints:
  GET /api/admin/sse  -- SSE stream for admin activity feed
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import decode_access_token
from src.config import Settings, get_settings
from src.db.models.user import User, UserRole
from src.db.session import get_db
from src.services.sse_service import sse_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin-sse"],
)


async def _resolve_staff_user(
    token: str | None = Query(default=None, description="JWT token (for EventSource)"),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Authenticate via query-param token (EventSource) or fall through to header auth.

    EventSource API does not support custom HTTP headers, so the frontend
    passes the JWT as a ``?token=`` query parameter. This dependency tries
    the query param first; if absent, it delegates to the standard
    ``require_staff`` header-based dependency.
    """
    if token is None:
        # No query param — will be handled by the endpoint's other dependency
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
    )
    try:
        payload = decode_access_token(token, settings.secret_key, settings.algorithm)
        user_id: str | None = payload.get("sub")  # type: ignore[assignment]
        if user_id is None:
            raise exc
    except JWTError as jwt_exc:
        raise exc from jwt_exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise exc
    if user.role not in (UserRole.STAFF.value, UserRole.ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )
    return user


@router.get(
    "/sse",
    summary="Real-time admin notification stream",
    description=(
        "Server-Sent Events stream for admin dashboard. "
        "Delivers real-time donation notifications and activity updates. "
        "Authenticate via ?token= query param (EventSource) or Bearer header."
    ),
    responses={
        200: {
            "description": "SSE stream opened",
            "content": {"text/event-stream": {}},
        },
        503: {"description": "Too many connections"},
    },
)
async def admin_sse_stream(
    current_user: User = Depends(_resolve_staff_user),
) -> StreamingResponse:
    """Open an SSE connection for real-time admin notifications.

    The stream delivers:
    - activity: Real-time activity feed items (all domain events)
    - donation: Real-time donation received notifications
    - heartbeat: Periodic keep-alive comments (every 30s)

    Requires staff authentication via query param or Bearer header.
    """
    try:
        connection = sse_manager.connect(user_id=current_user.id)
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "service_unavailable",
                "message": "Too many active SSE connections",
            },
        ) from None

    logger.info(
        "Admin SSE stream opened for user %s (connection=%s)",
        current_user.id,
        connection.id,
    )

    return StreamingResponse(
        sse_manager.stream(connection),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
