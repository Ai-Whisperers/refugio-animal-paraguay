"""Share tracking endpoints — record and analyze content sharing events.

Endpoints:
  POST /api/shares/track                -- record a share event (public)
  GET  /api/admin/shares/analytics      -- share analytics (staff)
  GET  /api/admin/shares/top            -- top shared content (staff)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.share_tracking_service import (
    InvalidEntityTypeError,
    InvalidPlatformError,
    ShareTrackingError,
    get_share_analytics,
    get_top_shared,
    track_share,
)

logger = logging.getLogger(__name__)

# Public share tracking router
public_router = APIRouter(
    prefix="/api/shares",
    tags=["shares"],
)

# Admin analytics router
admin_router = APIRouter(
    prefix="/api/admin/shares",
    tags=["shares-admin"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ShareTrackRequest(BaseModel):
    """Request body for tracking a share event."""

    entity_type: str = Field(
        ...,
        max_length=20,
        description="Type of shared entity (animal, campaign, story, blog_post)",
    )
    entity_id: UUID = Field(..., description="ID of the shared entity")
    platform: str = Field(
        ...,
        max_length=20,
        description="Sharing platform (whatsapp, facebook, twitter, copy_link, native_share)",
    )


class ShareTrackResponse(BaseModel):
    """Response for successful share tracking."""

    success: bool = True


class ShareAnalyticsResponse(BaseModel):
    """Response for share analytics."""

    total_shares: int
    shares_by_platform: dict[str, int]
    shares_by_entity_type: dict[str, int]
    daily_shares: list[dict]
    period_days: int


class TopSharedItemResponse(BaseModel):
    """Single top-shared entity."""

    entity_id: str
    entity_type: str
    share_count: int
    platforms: dict[str, int]


class TopSharedResponse(BaseModel):
    """List of top-shared entities."""

    items: list[TopSharedItemResponse]
    entity_type: str
    period_days: int


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def _handle_share_error(exc: ShareTrackingError) -> HTTPException:
    """Map share tracking errors to HTTP responses."""
    if isinstance(exc, (InvalidEntityTypeError, InvalidPlatformError)):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "validation_error", "message": exc.message, "details": exc.details},
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"error": "validation_error", "message": exc.message, "details": exc.details},
    )


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@public_router.post(
    "/track",
    response_model=ShareTrackResponse,
    status_code=status.HTTP_200_OK,
    summary="Track a share event",
)
async def track_share_endpoint(
    body: ShareTrackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ShareTrackResponse:
    """Record a content share event (public, no auth required)."""
    # Extract client IP for logging/fraud detection
    ip_address = request.client.host if request.client else None

    try:
        await track_share(
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            platform=body.platform,
            ip_address=ip_address,
            db=db,
        )
    except ShareTrackingError as exc:
        raise _handle_share_error(exc) from None

    await db.commit()
    return ShareTrackResponse(success=True)


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@admin_router.get(
    "/analytics",
    response_model=ShareAnalyticsResponse,
    summary="Get share analytics",
)
async def get_analytics_endpoint(
    entity_type: str | None = Query(None, description="Filter by entity type"),
    days: int = Query(30, ge=1, le=365, description="Analytics period in days"),
    _staff_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> ShareAnalyticsResponse:
    """Get share analytics with breakdowns (staff only)."""
    try:
        analytics = await get_share_analytics(
            db,
            entity_type=entity_type,
            days=days,
        )
    except ShareTrackingError as exc:
        raise _handle_share_error(exc) from None

    return ShareAnalyticsResponse(**analytics)


@admin_router.get(
    "/top",
    response_model=TopSharedResponse,
    summary="Get top shared content",
)
async def get_top_shared_endpoint(
    entity_type: str = Query(..., description="Entity type to rank"),
    days: int = Query(30, ge=1, le=365, description="Analytics period in days"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    _staff_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> TopSharedResponse:
    """Get top shared entities ranked by share count (staff only)."""
    try:
        items = await get_top_shared(
            db,
            entity_type=entity_type,
            days=days,
            limit=limit,
        )
    except ShareTrackingError as exc:
        raise _handle_share_error(exc) from None

    return TopSharedResponse(
        items=[TopSharedItemResponse(**item) for item in items],
        entity_type=entity_type,
        period_days=days,
    )
