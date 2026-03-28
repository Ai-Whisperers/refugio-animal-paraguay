"""Community feed service — aggregates recent activity across animals, campaigns, needs, and success stories."""

from __future__ import annotations

import logging
import math
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.animal import Animal, AnimalStatus
from src.db.models.campaign import Campaign, CampaignStatus
from src.db.models.community_need import CommunityNeed, NeedStatus
from src.db.models.success_story import SuccessStory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FEED_PAGE_SIZE = 20
# Fetch this many items per source before merging — larger window so merge
# result has enough items after filtering.
SOURCE_FETCH_LIMIT = 100


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class FeedItemType(StrEnum):
    ANIMAL = "animal"
    CAMPAIGN = "campaign"
    NEED = "need"
    SUCCESS = "success"


FEED_BADGE: dict[FeedItemType, str] = {
    FeedItemType.ANIMAL: "New Arrival",
    FeedItemType.CAMPAIGN: "Active Campaign",
    FeedItemType.NEED: "Help Needed",
    FeedItemType.SUCCESS: "Adoption Success",
}


# ---------------------------------------------------------------------------
# Haversine helper
# ---------------------------------------------------------------------------


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two lat/lon points."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return r * 2 * math.asin(math.sqrt(a))


def _within_radius(
    coords: dict[str, Any] | None,
    lat: float | None,
    lng: float | None,
    radius_km: float,
) -> bool:
    """Return True if coords JSON is within radius_km of (lat, lng), or if no filtering requested."""
    if lat is None or lng is None:
        return True
    if coords is None:
        # Items without location pass through (inclusive by design)
        return True
    item_lat = coords.get("lat") or coords.get("latitude")
    item_lng = coords.get("lng") or coords.get("lon") or coords.get("longitude")
    if item_lat is None or item_lng is None:
        return True
    return _haversine_km(lat, lng, float(item_lat), float(item_lng)) <= radius_km


# ---------------------------------------------------------------------------
# Per-source fetchers
# ---------------------------------------------------------------------------


async def _fetch_animals(db: AsyncSession, limit: int) -> list[dict[str, Any]]:
    """Fetch recently available/intake animals."""
    stmt = (
        select(Animal)
        .where(Animal.status.in_([AnimalStatus.AVAILABLE, "intake"]))
        .order_by(Animal.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    items: list[dict[str, Any]] = []
    for animal in rows:
        preview = (animal.description or "")[:150]
        if len(animal.description or "") > 150:
            preview += "…"
        items.append(
            {
                "id": str(animal.id),
                "event_type": FeedItemType.ANIMAL,
                "title": f"{animal.name} is looking for a home",
                "preview": preview or f"{animal.species.capitalize()} available for adoption.",
                "timestamp": animal.created_at,
                "image_url": animal.primary_photo_url,
                "detail_url": f"/animals/{animal.id}",
                "rescuer_name": None,
                "location_city": None,
                "location_coords": None,
                "badge": FEED_BADGE[FeedItemType.ANIMAL],
                "species": animal.species,
                "breed": animal.breed,
            }
        )
    return items


async def _fetch_campaigns(db: AsyncSession, limit: int) -> list[dict[str, Any]]:
    """Fetch active campaigns."""
    stmt = (
        select(Campaign)
        .where(Campaign.status == CampaignStatus.ACTIVE)
        .order_by(Campaign.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    items: list[dict[str, Any]] = []
    for campaign in rows:
        preview = (campaign.description or "")[:150]
        if len(campaign.description or "") > 150:
            preview += "…"
        target_eur = campaign.target_amount_cents / 100
        items.append(
            {
                "id": str(campaign.id),
                "event_type": FeedItemType.CAMPAIGN,
                "title": campaign.title,
                "preview": preview,
                "timestamp": campaign.created_at,
                "image_url": campaign.image_url,
                "detail_url": f"/campaigns/{campaign.id}",
                "rescuer_name": None,
                "location_city": None,
                "location_coords": None,
                "badge": FEED_BADGE[FeedItemType.CAMPAIGN],
                "target_eur": target_eur,
                "fund_category": campaign.fund_category,
            }
        )
    return items


async def _fetch_needs(db: AsyncSession, limit: int) -> list[dict[str, Any]]:
    """Fetch open community needs."""
    stmt = (
        select(CommunityNeed)
        .where(CommunityNeed.status == NeedStatus.OPEN)
        .order_by(CommunityNeed.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    items: list[dict[str, Any]] = []
    for need in rows:
        preview = (need.description or "")[:150]
        if len(need.description or "") > 150:
            preview += "…"
        items.append(
            {
                "id": str(need.id),
                "event_type": FeedItemType.NEED,
                "title": need.title,
                "preview": preview,
                "timestamp": need.created_at,
                "image_url": need.image_url,
                "detail_url": f"/needs/{need.id}",
                "rescuer_name": None,
                "location_city": None,
                "location_coords": None,
                "badge": FEED_BADGE[FeedItemType.NEED],
                "category": need.category,
                "estimated_cost_cents": need.estimated_cost_cents,
                "currency": need.currency,
            }
        )
    return items


async def _fetch_success_stories(db: AsyncSession, limit: int) -> list[dict[str, Any]]:
    """Fetch published success stories."""
    stmt = (
        select(SuccessStory)
        .where(
            SuccessStory.is_deleted.is_(False),
            SuccessStory.published_at.isnot(None),
        )
        .order_by(SuccessStory.published_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    items: list[dict[str, Any]] = []
    for story in rows:
        preview = (story.quote or story.story_text or "")[:150]
        if len(story.quote or story.story_text or "") > 150:
            preview += "…"
        items.append(
            {
                "id": str(story.id),
                "event_type": FeedItemType.SUCCESS,
                "title": story.title,
                "preview": preview,
                "timestamp": story.published_at,
                "image_url": story.photo_url,
                "detail_url": f"/stories/{story.id}",
                "rescuer_name": None,
                "location_city": None,
                "location_coords": None,
                "badge": FEED_BADGE[FeedItemType.SUCCESS],
                "adopter_name": story.adopter_name,
                "is_featured": story.is_featured,
            }
        )
    return items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_community_feed(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = FEED_PAGE_SIZE,
    item_types: list[FeedItemType] | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float = 100.0,
) -> dict[str, Any]:
    """Return paginated community feed aggregated from animals, campaigns, needs, and success stories.

    Args:
        db: Async SQLAlchemy session.
        page: 1-based page number.
        page_size: Items per page (max 50, default 20).
        item_types: Subset of feed item types to include; None means all types.
        lat: Latitude for location-based filtering (degrees).
        lng: Longitude for location-based filtering (degrees).
        radius_km: Radius in km for location filter (default 100).

    Returns:
        Dict with keys: items, total, page, page_size, has_next.
    """
    page_size = min(page_size, 50)
    enabled: set[FeedItemType] = set(item_types) if item_types else set(FeedItemType)

    # Fetch from each enabled source
    tasks: list[list[dict[str, Any]]] = []
    if FeedItemType.ANIMAL in enabled:
        tasks.append(await _fetch_animals(db, SOURCE_FETCH_LIMIT))
    if FeedItemType.CAMPAIGN in enabled:
        tasks.append(await _fetch_campaigns(db, SOURCE_FETCH_LIMIT))
    if FeedItemType.NEED in enabled:
        tasks.append(await _fetch_needs(db, SOURCE_FETCH_LIMIT))
    if FeedItemType.SUCCESS in enabled:
        tasks.append(await _fetch_success_stories(db, SOURCE_FETCH_LIMIT))

    # Merge and apply location filter
    all_items: list[dict[str, Any]] = []
    for source_items in tasks:
        for item in source_items:
            if _within_radius(item.get("location_coords"), lat, lng, radius_km):
                all_items.append(item)

    # Sort by timestamp descending
    all_items.sort(key=lambda x: x["timestamp"] or datetime.min, reverse=True)

    # Paginate
    total = len(all_items)
    offset = (page - 1) * page_size
    page_items = all_items[offset : offset + page_size]

    return {
        "items": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": offset + page_size < total,
    }
