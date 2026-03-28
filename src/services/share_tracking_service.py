"""Share tracking service — record and analyze content sharing events.

Provides share event recording, analytics aggregation, and top-shared
content rankings. Events are immutable (event-sourcing pattern).
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.share_event import ShareEntityType, ShareEvent, SharePlatform

logger = logging.getLogger(__name__)

# Validation
VALID_ENTITY_TYPES = frozenset({t.value for t in ShareEntityType})
VALID_PLATFORMS = frozenset({p.value for p in SharePlatform})

# Analytics defaults
DEFAULT_ANALYTICS_DAYS = 30
TOP_SHARED_LIMIT = 10


class ShareTrackingError(Exception):
    """Base error for share tracking operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidEntityTypeError(ShareTrackingError):
    """Raised for invalid entity type."""

    def __init__(self, entity_type: str) -> None:
        super().__init__(
            message="Invalid entity type",
            details=f"Must be one of: {', '.join(sorted(VALID_ENTITY_TYPES))}",
        )


class InvalidPlatformError(ShareTrackingError):
    """Raised for invalid platform."""

    def __init__(self, platform: str) -> None:
        super().__init__(
            message="Invalid platform",
            details=f"Must be one of: {', '.join(sorted(VALID_PLATFORMS))}",
        )


def validate_entity_type(entity_type: str) -> None:
    """Validate entity type."""
    if entity_type not in VALID_ENTITY_TYPES:
        raise InvalidEntityTypeError(entity_type)


def validate_platform(platform: str) -> None:
    """Validate sharing platform."""
    if platform not in VALID_PLATFORMS:
        raise InvalidPlatformError(platform)


async def track_share(
    *,
    entity_type: str,
    entity_id: UUID,
    platform: str,
    sharer_user_id: UUID | None = None,
    ip_address: str | None = None,
    db: AsyncSession,
) -> ShareEvent:
    """Record a share event.

    Raises:
        InvalidEntityTypeError: If entity type is invalid.
        InvalidPlatformError: If platform is invalid.
    """
    validate_entity_type(entity_type)
    validate_platform(platform)

    event = ShareEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        platform=platform,
        sharer_user_id=sharer_user_id,
        ip_address=ip_address,
    )

    db.add(event)
    await db.flush()

    logger.info(
        "Share event tracked: entity=%s/%s platform=%s",
        entity_type,
        entity_id,
        platform,
    )
    return event


async def get_share_analytics(
    db: AsyncSession,
    *,
    entity_type: str | None = None,
    days: int = DEFAULT_ANALYTICS_DAYS,
) -> dict:
    """Get share analytics with breakdowns by platform and entity type.

    Returns dict with total_shares, shares_by_platform, shares_by_entity_type,
    and daily_shares time series.
    """
    if entity_type:
        validate_entity_type(entity_type)

    since = datetime.now(UTC) - timedelta(days=days)

    # Base filter
    base_filter = ShareEvent.created_at >= since
    if entity_type:
        base_filter = (ShareEvent.created_at >= since) & (ShareEvent.entity_type == entity_type)

    # Total shares
    total_result = await db.execute(select(func.count(ShareEvent.id)).where(base_filter))
    total_shares = total_result.scalar_one()

    # Shares by platform
    platform_result = await db.execute(
        select(ShareEvent.platform, func.count(ShareEvent.id))
        .where(base_filter)
        .group_by(ShareEvent.platform)
        .order_by(func.count(ShareEvent.id).desc())
    )
    shares_by_platform = {row[0]: row[1] for row in platform_result.all()}

    # Shares by entity type
    entity_result = await db.execute(
        select(ShareEvent.entity_type, func.count(ShareEvent.id))
        .where(base_filter)
        .group_by(ShareEvent.entity_type)
        .order_by(func.count(ShareEvent.id).desc())
    )
    shares_by_entity_type = {row[0]: row[1] for row in entity_result.all()}

    # Daily shares (time series for last N days)
    daily_result = await db.execute(
        select(
            func.date_trunc("day", ShareEvent.created_at).label("day"),
            func.count(ShareEvent.id),
        )
        .where(base_filter)
        .group_by("day")
        .order_by("day")
    )
    daily_shares = [
        {"date": str(row[0].date()) if row[0] else None, "count": row[1]}
        for row in daily_result.all()
    ]

    return {
        "total_shares": total_shares,
        "shares_by_platform": shares_by_platform,
        "shares_by_entity_type": shares_by_entity_type,
        "daily_shares": daily_shares,
        "period_days": days,
    }


async def get_top_shared(
    db: AsyncSession,
    *,
    entity_type: str,
    days: int = DEFAULT_ANALYTICS_DAYS,
    limit: int = TOP_SHARED_LIMIT,
) -> list[dict]:
    """Get top shared entities ranked by share count.

    Returns list of {entity_id, entity_type, share_count, platforms} dicts.
    """
    validate_entity_type(entity_type)

    since = datetime.now(UTC) - timedelta(days=days)

    result = await db.execute(
        select(
            ShareEvent.entity_id,
            func.count(ShareEvent.id).label("share_count"),
        )
        .where(
            ShareEvent.entity_type == entity_type,
            ShareEvent.created_at >= since,
        )
        .group_by(ShareEvent.entity_id)
        .order_by(func.count(ShareEvent.id).desc())
        .limit(limit)
    )

    items = []
    for row in result.all():
        # Get platform breakdown for this entity
        platform_result = await db.execute(
            select(ShareEvent.platform, func.count(ShareEvent.id))
            .where(
                ShareEvent.entity_id == row[0],
                ShareEvent.entity_type == entity_type,
                ShareEvent.created_at >= since,
            )
            .group_by(ShareEvent.platform)
        )
        platforms = {p_row[0]: p_row[1] for p_row in platform_result.all()}

        items.append(
            {
                "entity_id": str(row[0]),
                "entity_type": entity_type,
                "share_count": row[1],
                "platforms": platforms,
            }
        )

    return items
