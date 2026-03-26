"""Business logic for fundraising campaign management.

Handles campaign CRUD, status transitions, and donation progress tracking.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.campaign import Campaign, CampaignStatus
from src.db.models.donation import Donation, DonationStatus

logger = logging.getLogger(__name__)


async def create_campaign(
    db: AsyncSession,
    title: str,
    goal_amount_cents: int,
    currency: str = "USD",
    category: str = "other",
    description: str | None = None,
    deadline: object = None,
    featured: bool = False,
    created_by_user_id: UUID | None = None,
) -> Campaign:
    """Create a new fundraising campaign in draft status."""
    campaign = Campaign(
        title=title,
        description=description,
        goal_amount_cents=goal_amount_cents,
        currency=currency,
        category=category,
        status=CampaignStatus.DRAFT.value,
        featured=featured,
        deadline=deadline,
        created_by_user_id=created_by_user_id,
    )
    db.add(campaign)
    await db.flush()

    logger.info("Created campaign '%s' (goal: %d cents %s)", title, goal_amount_cents, currency)
    return campaign


async def update_campaign(
    db: AsyncSession,
    campaign_id: UUID,
    title: str | None = None,
    description: str | None = None,
    goal_amount_cents: int | None = None,
    category: str | None = None,
    status: str | None = None,
    deadline: object = None,
    featured: bool | None = None,
) -> Campaign | None:
    """Update campaign fields. Returns None if not found."""
    campaign = await db.get(Campaign, campaign_id)
    if campaign is None:
        return None

    if title is not None:
        campaign.title = title
    if description is not None:
        campaign.description = description
    if goal_amount_cents is not None:
        campaign.goal_amount_cents = goal_amount_cents
    if category is not None:
        campaign.category = category
    if status is not None:
        campaign.status = status
    if deadline is not None:
        campaign.deadline = deadline  # type: ignore[assignment]
    if featured is not None:
        campaign.featured = featured

    await db.flush()
    logger.info("Updated campaign %s", campaign_id)
    return campaign


async def get_campaign(
    db: AsyncSession,
    campaign_id: UUID,
) -> Campaign | None:
    """Get a campaign by ID."""
    return await db.get(Campaign, campaign_id)


async def list_campaigns(
    db: AsyncSession,
    status_filter: str | None = None,
    featured_only: bool = False,
) -> list[Campaign]:
    """List campaigns with optional filters."""
    stmt = select(Campaign).order_by(Campaign.created_at.desc())

    if status_filter:
        stmt = stmt.where(Campaign.status == status_filter)
    if featured_only:
        stmt = stmt.where(Campaign.featured.is_(True))

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_campaign_progress(
    db: AsyncSession,
    campaign_id: UUID,
) -> dict[str, int]:
    """Calculate campaign fundraising progress.

    Returns dict with raised_amount_cents, donor_count.
    Only counts completed donations.
    """
    stmt = select(
        func.coalesce(func.sum(Donation.amount_cents), 0).label("raised"),
        func.count(func.distinct(Donation.donor_id)).label("donors"),
    ).where(
        Donation.campaign_id == campaign_id,
        Donation.status == DonationStatus.COMPLETED.value,
    )
    result = await db.execute(stmt)
    row = result.one()

    return {
        "raised_amount_cents": int(row.raised),
        "donor_count": int(row.donors),
    }


async def delete_campaign(
    db: AsyncSession,
    campaign_id: UUID,
) -> bool:
    """Delete a campaign (only draft campaigns can be deleted).

    Returns True if deleted, False if not found or not in draft status.
    """
    campaign = await db.get(Campaign, campaign_id)
    if campaign is None:
        return False

    if campaign.status != CampaignStatus.DRAFT.value:
        return False

    await db.delete(campaign)
    await db.flush()

    logger.info("Deleted draft campaign %s", campaign_id)
    return True
