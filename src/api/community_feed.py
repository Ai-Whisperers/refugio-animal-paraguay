"""Community feed public API.

Public endpoints:
  GET  /api/community/feed  -- paginated activity feed (animals, campaigns, needs, success stories)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_async_session
from src.services.community_feed_service import (
    FEED_PAGE_SIZE,
    FeedItemType,
    get_community_feed,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/community", tags=["community-feed"])

# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

VALID_ITEM_TYPES = {t.value for t in FeedItemType}


class FeedItemResponse(BaseModel):
    """A single activity item in the community feed."""

    id: str
    event_type: str
    title: str
    preview: str
    timestamp: Any  # datetime — kept as Any to allow ISO serialisation
    image_url: str | None
    detail_url: str
    rescuer_name: str | None
    location_city: str | None
    badge: str

    # Type-specific extras (present based on event_type)
    species: str | None = None
    breed: str | None = None
    target_eur: float | None = None
    fund_category: str | None = None
    category: str | None = None
    estimated_cost_cents: int | None = None
    currency: str | None = None
    adopter_name: str | None = None
    is_featured: bool | None = None


class FeedResponse(BaseModel):
    """Paginated community feed response."""

    items: list[FeedItemResponse]
    total: int
    page: int
    page_size: int
    has_next: bool = Field(..., description="Whether more pages exist after this one")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/feed", response_model=FeedResponse, summary="Community activity feed")
async def list_community_feed(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(FEED_PAGE_SIZE, ge=1, le=50, description="Items per page"),
    types: list[str] | None = Query(
        None,
        description="Filter by item type: animal, campaign, need, success. Repeatable.",
    ),
    lat: float | None = Query(None, description="Latitude for location filter"),
    lng: float | None = Query(None, description="Longitude for location filter"),
    radius_km: float = Query(100.0, ge=1, le=5000, description="Radius in km for location filter"),
    db: AsyncSession = Depends(get_async_session),
) -> FeedResponse:
    """Return paginated community activity feed.

    Aggregates recent animals, active campaigns, open needs, and success stories.
    Supports filtering by item type and location radius.
    """
    # Validate and coerce type filter
    parsed_types: list[FeedItemType] | None = None
    if types:
        valid = [t for t in types if t in VALID_ITEM_TYPES]
        if valid:
            parsed_types = [FeedItemType(t) for t in valid]

    result = await get_community_feed(
        db,
        page=page,
        page_size=page_size,
        item_types=parsed_types,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
    )

    items = [FeedItemResponse(**item) for item in result["items"]]
    return FeedResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        has_next=result["has_next"],
    )
