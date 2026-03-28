"""Service layer for rescuer campaign management.

Provides CRUD operations for rescuer-owned campaigns with auto-approval logic
for verified rescuers and donation aggregation for progress tracking.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.campaign import Campaign, CampaignStatus
from src.db.models.donation import Donation
from src.db.models.rescuer_profile import RescuerProfile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RescuerNotFoundError(Exception):
    """Raised when no rescuer profile exists for the user."""


class RescuerCampaignNotFoundError(Exception):
    """Raised when the campaign does not exist."""


class RescuerCampaignPermissionError(Exception):
    """Raised when the rescuer does not own the campaign."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _campaign_to_dict(campaign: Campaign, raised_cents: int, donor_count: int) -> dict:
    """Serialize a Campaign ORM object to a response dict."""
    return {
        "id": campaign.id,
        "title": campaign.title,
        "description": campaign.description,
        "target_amount_eur": campaign.target_amount_cents / 100,
        "raised_amount_eur": raised_cents / 100,
        "donor_count": donor_count,
        "fund_category": campaign.fund_category,
        "status": campaign.status,
        "goal_message": campaign.goal_message,
        "animal_ids": campaign.animal_ids or [],
        "photo_urls": campaign.photo_urls or [],
        "deadline": campaign.deadline,
        "requires_approval": campaign.requires_approval,
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at,
    }


async def _get_rescuer_by_user(user_id: UUID, db: AsyncSession) -> RescuerProfile:
    """Fetch the rescuer profile for a user, raising RescuerNotFoundError if missing."""
    result = await db.execute(select(RescuerProfile).where(RescuerProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise RescuerNotFoundError(f"No rescuer profile for user {user_id}")
    return profile


async def _aggregate_campaign_donations(campaign_id: UUID, db: AsyncSession) -> tuple[int, int]:
    """Return (raised_cents, donor_count) for a campaign using target_type='campaign'."""
    result = await db.execute(
        select(
            func.coalesce(func.sum(Donation.amount_cents), 0),
            func.count(Donation.id),
        ).where(
            Donation.target_type == "campaign",
            Donation.target_id == campaign_id,
        )
    )
    row = result.one()
    return int(row[0]), int(row[1])


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def list_rescuer_campaigns(
    user_id: UUID,
    page: int,
    page_size: int,
    db: AsyncSession,
) -> dict:
    """Return paginated campaigns owned by the rescuer.

    Args:
        user_id: Authenticated user's UUID.
        page: 1-based page number.
        page_size: Results per page.
        db: Database session.

    Returns:
        dict with keys: campaigns (list of dicts), total (int).

    Raises:
        RescuerNotFoundError: If user has no rescuer profile.
    """
    rescuer = await _get_rescuer_by_user(user_id, db)

    count_result = await db.execute(
        select(func.count(Campaign.id)).where(Campaign.rescuer_id == rescuer.id)
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    campaigns_result = await db.execute(
        select(Campaign)
        .where(Campaign.rescuer_id == rescuer.id)
        .order_by(Campaign.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    campaigns = campaigns_result.scalars().all()

    campaign_dicts = []
    for c in campaigns:
        raised, donors = await _aggregate_campaign_donations(c.id, db)
        campaign_dicts.append(_campaign_to_dict(c, raised, donors))

    return {"campaigns": campaign_dicts, "total": total}


async def create_rescuer_campaign(
    user_id: UUID,
    title: str,
    description: str,
    target_amount_eur: float,
    fund_category: str,
    goal_message: str | None,
    animal_ids: list[str],
    photo_urls: list[str],
    deadline: datetime | None,
    db: AsyncSession,
) -> dict:
    """Create a campaign for the authenticated rescuer.

    Verified rescuers get status=active immediately.
    Unverified rescuers get status=draft with requires_approval=True.

    Args:
        user_id: Authenticated user's UUID.
        title: Campaign title.
        description: Full description text.
        target_amount_eur: Target in EUR (converted to cents internally).
        fund_category: One of the FundCategory values.
        goal_message: Short motivational message (optional).
        animal_ids: List of animal UUIDs as strings.
        photo_urls: List of photo URLs.
        deadline: Optional campaign deadline.
        db: Database session.

    Returns:
        Serialized campaign dict.

    Raises:
        RescuerNotFoundError: If user has no rescuer profile.
    """
    rescuer = await _get_rescuer_by_user(user_id, db)

    # Auto-approve verified rescuers; unverified go to draft for admin review
    is_verified = rescuer.is_verified
    initial_status = CampaignStatus.ACTIVE if is_verified else CampaignStatus.DRAFT
    requires_approval = not is_verified

    campaign = Campaign(
        title=title,
        description=description,
        target_amount_cents=int(target_amount_eur * 100),
        currency="EUR",
        fund_category=fund_category,
        status=initial_status.value,
        rescuer_id=rescuer.id,
        goal_message=goal_message,
        animal_ids=[UUID(aid) for aid in animal_ids] if animal_ids else [],
        photo_urls=photo_urls or [],
        deadline=deadline,
        requires_approval=requires_approval,
        allow_overfunding=True,
    )
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)

    logger.info(
        "Rescuer campaign created",
        extra={
            "campaign_id": str(campaign.id),
            "rescuer_id": str(rescuer.id),
            "status": campaign.status,
            "requires_approval": requires_approval,
        },
    )

    return _campaign_to_dict(campaign, 0, 0)


async def get_rescuer_campaign(
    user_id: UUID,
    campaign_id: UUID,
    db: AsyncSession,
) -> dict:
    """Fetch a single campaign owned by the rescuer.

    Raises:
        RescuerNotFoundError: No rescuer profile.
        RescuerCampaignNotFoundError: Campaign does not exist.
        RescuerCampaignPermissionError: Campaign belongs to a different rescuer.
    """
    rescuer = await _get_rescuer_by_user(user_id, db)

    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise RescuerCampaignNotFoundError(str(campaign_id))
    if campaign.rescuer_id != rescuer.id:
        raise RescuerCampaignPermissionError(str(campaign_id))

    raised, donors = await _aggregate_campaign_donations(campaign.id, db)
    return _campaign_to_dict(campaign, raised, donors)


async def end_rescuer_campaign(
    user_id: UUID,
    campaign_id: UUID,
    action: str,
    impact_message: str | None,
    db: AsyncSession,
) -> dict:
    """Complete or archive a rescuer campaign.

    Args:
        user_id: Authenticated user's UUID.
        campaign_id: Campaign to update.
        action: 'complete' → status=completed, 'archive' → status=archived.
        impact_message: Optional message to log (donor notification is async/future).
        db: Database session.

    Raises:
        RescuerNotFoundError, RescuerCampaignNotFoundError, RescuerCampaignPermissionError.
    """
    rescuer = await _get_rescuer_by_user(user_id, db)

    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise RescuerCampaignNotFoundError(str(campaign_id))
    if campaign.rescuer_id != rescuer.id:
        raise RescuerCampaignPermissionError(str(campaign_id))

    new_status = CampaignStatus.COMPLETED if action == "complete" else CampaignStatus.ARCHIVED
    campaign.status = new_status.value
    campaign.updated_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(campaign)

    logger.info(
        "Rescuer campaign ended",
        extra={
            "campaign_id": str(campaign.id),
            "rescuer_id": str(rescuer.id),
            "new_status": campaign.status,
            "impact_message_provided": impact_message is not None,
        },
    )

    raised, donors = await _aggregate_campaign_donations(campaign.id, db)
    return _campaign_to_dict(campaign, raised, donors)


async def get_public_campaign_detail(
    rescuer_slug: str,
    campaign_id: UUID,
    db: AsyncSession,
) -> dict:
    """Fetch public campaign detail for display on the campaign page.

    Includes rescuer info, progress bar data, and recent donors.

    Raises:
        RescuerNotFoundError: Rescuer with slug not found.
        RescuerCampaignNotFoundError: Campaign not found or not owned by this rescuer.
    """
    rescuer_result = await db.execute(
        select(RescuerProfile).where(RescuerProfile.slug == rescuer_slug)
    )
    rescuer = rescuer_result.scalar_one_or_none()
    if rescuer is None:
        raise RescuerNotFoundError(rescuer_slug)

    campaign_result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.rescuer_id == rescuer.id,
        )
    )
    campaign = campaign_result.scalar_one_or_none()
    if campaign is None:
        raise RescuerCampaignNotFoundError(str(campaign_id))

    raised_cents, donor_count = await _aggregate_campaign_donations(campaign.id, db)
    raised_eur = raised_cents / 100
    target_eur = campaign.target_amount_cents / 100
    progress_pct = min(round((raised_eur / target_eur) * 100, 1) if target_eur > 0 else 0.0, 100.0)

    # Fetch up to 5 most recent donations to this campaign
    donors_result = await db.execute(
        select(Donation)
        .where(
            Donation.target_type == "campaign",
            Donation.target_id == campaign.id,
        )
        .order_by(Donation.created_at.desc())
        .limit(5)
    )
    recent_donations = donors_result.scalars().all()
    recent_donors = [
        {
            "donor_name": "Anónimo",
            "amount_eur": d.amount_cents / 100,
            "donated_at": d.created_at.isoformat(),
        }
        for d in recent_donations
    ]

    return {
        "id": campaign.id,
        "rescuer_slug": rescuer.slug,
        "rescuer_name": rescuer.display_name,
        "rescuer_verified": rescuer.is_verified,
        "title": campaign.title,
        "description": campaign.description,
        "target_amount_eur": target_eur,
        "raised_amount_eur": raised_eur,
        "progress_pct": progress_pct,
        "donor_count": donor_count,
        "fund_category": campaign.fund_category,
        "status": campaign.status,
        "goal_message": campaign.goal_message,
        "photo_urls": campaign.photo_urls or [],
        "deadline": campaign.deadline,
        "recent_donors": recent_donors,
        "created_at": campaign.created_at,
    }
