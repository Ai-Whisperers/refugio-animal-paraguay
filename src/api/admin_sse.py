"""Server-Sent Events endpoint for real-time admin notifications.

Provides a streaming SSE connection for the admin dashboard to receive
real-time donation notifications and other activity updates.

Endpoints:
  GET /api/admin/sse  -- SSE stream for admin activity feed
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.services.sse_service import sse_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["admin-sse"],
)


@router.get(
    "/sse",
    summary="Real-time admin notification stream",
    description=(
        "Server-Sent Events stream for admin dashboard. "
        "Delivers real-time donation notifications and activity updates."
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
    current_user: User = Depends(require_staff),
) -> StreamingResponse:
    """Open an SSE connection for real-time admin notifications.

    The stream delivers:
    - donation: Real-time donation received notifications
    - heartbeat: Periodic keep-alive comments (every 30s)

    Requires staff authentication.
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
