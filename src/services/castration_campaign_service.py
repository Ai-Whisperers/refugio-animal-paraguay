"""Service for managing castration campaigns.

Handles CRUD for castration campaigns, partner clinic management,
completed count increments, and status computation.
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.castration_campaign import (
    CastrationCampaign,
    CastrationCampaignClinic,
)
from src.db.models.vet_clinic import VetClinic

logger = logging.getLogger(__name__)

# Validation constants
MIN_TITLE_LENGTH = 5
MAX_TITLE_LENGTH = 200
MIN_DESCRIPTION_LENGTH = 10
MAX_DESCRIPTION_LENGTH = 1000


class CampaignNotFoundError(Exception):
    """Raised when a castration campaign is not found."""

    def __init__(self, campaign_id: UUID) -> None:
        self.campaign_id = campaign_id
        self.message = f"Castration campaign {campaign_id} not found."
        super().__init__(self.message)


class InvalidCampaignError(Exception):
    """Raised when campaign data fails validation."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        self.message = f"Invalid campaign: {detail}"
        super().__init__(self.message)


class ClinicNotFoundError(Exception):
    """Raised when a referenced vet clinic does not exist."""

    def __init__(self, clinic_id: UUID) -> None:
        self.clinic_id = clinic_id
        self.message = f"Vet clinic {clinic_id} not found."
        super().__init__(self.message)


def validate_campaign_data(
    *,
    title: str,
    description: str,
    target_count: int,
    start_date: date,
    end_date: date,
    partner_clinic_ids: list[UUID],
) -> None:
    """Validate campaign creation/update data.

    Raises InvalidCampaignError if any validation fails.
    """
    if not title or len(title) < MIN_TITLE_LENGTH or len(title) > MAX_TITLE_LENGTH:
        raise InvalidCampaignError(
            f"Title must be between {MIN_TITLE_LENGTH} and {MAX_TITLE_LENGTH} characters."
        )

    if not description or len(description) < MIN_DESCRIPTION_LENGTH:
        raise InvalidCampaignError(
            f"Description must be at least {MIN_DESCRIPTION_LENGTH} characters."
        )
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise InvalidCampaignError(
            f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters."
        )

    if target_count <= 0:
        raise InvalidCampaignError("Target count must be greater than 0.")

    if end_date <= start_date:
        raise InvalidCampaignError("End date must be after start date.")

    if not partner_clinic_ids:
        raise InvalidCampaignError("At least one partner clinic is required.")


async def _verify_clinics_exist(db: AsyncSession, clinic_ids: list[UUID]) -> None:
    """Verify all clinic IDs reference existing vet clinics."""
    for clinic_id in clinic_ids:
        clinic = await db.get(VetClinic, clinic_id)
        if clinic is None:
            raise ClinicNotFoundError(clinic_id)


async def create_castration_campaign(
    db: AsyncSession,
    *,
    title: str,
    description: str,
    target_count: int,
    target_area: str,
    start_date: date,
    end_date: date,
    partner_clinic_ids: list[UUID],
    goal_message: str | None = None,
    created_by_id: UUID | None = None,
) -> CastrationCampaign:
    """Create a new castration campaign with partner clinics."""
    validate_campaign_data(
        title=title,
        description=description,
        target_count=target_count,
        start_date=start_date,
        end_date=end_date,
        partner_clinic_ids=partner_clinic_ids,
    )

    await _verify_clinics_exist(db, partner_clinic_ids)

    campaign = CastrationCampaign(
        title=title,
        description=description,
        goal_message=goal_message,
        target_count=target_count,
        target_area=target_area,
        start_date=start_date,
        end_date=end_date,
        created_by_id=created_by_id,
    )
    db.add(campaign)
    await db.flush()

    # Add partner clinic associations
    for clinic_id in partner_clinic_ids:
        junction = CastrationCampaignClinic(
            campaign_id=campaign.id,
            clinic_id=clinic_id,
        )
        db.add(junction)

    await db.flush()
    await db.refresh(campaign)

    logger.info("Created castration campaign: %s (%s)", campaign.id, title)
    return campaign


async def get_castration_campaign(db: AsyncSession, campaign_id: UUID) -> CastrationCampaign:
    """Fetch a castration campaign by ID. Raises CampaignNotFoundError if missing."""
    campaign = await db.get(CastrationCampaign, campaign_id)
    if campaign is None:
        raise CampaignNotFoundError(campaign_id)
    return campaign


async def list_castration_campaigns(db: AsyncSession) -> list[CastrationCampaign]:
    """List all castration campaigns ordered by start_date descending."""
    query = select(CastrationCampaign).order_by(CastrationCampaign.start_date.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_castration_campaign(
    db: AsyncSession,
    campaign_id: UUID,
    *,
    title: str | None = None,
    description: str | None = None,
    goal_message: str | None = None,
    target_count: int | None = None,
    target_area: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    partner_clinic_ids: list[UUID] | None = None,
) -> CastrationCampaign:
    """Update a castration campaign's details.

    completed_count is read-only and cannot be updated through this function.
    """
    campaign = await get_castration_campaign(db, campaign_id)

    # Apply updates
    new_title = title if title is not None else campaign.title
    new_description = description if description is not None else campaign.description
    new_target_count = target_count if target_count is not None else campaign.target_count
    new_start_date = start_date if start_date is not None else campaign.start_date
    new_end_date = end_date if end_date is not None else campaign.end_date
    new_clinic_ids = partner_clinic_ids if partner_clinic_ids is not None else None

    # Validate with merged values
    validate_campaign_data(
        title=new_title,
        description=new_description,
        target_count=new_target_count,
        start_date=new_start_date,
        end_date=new_end_date,
        partner_clinic_ids=new_clinic_ids or [UUID(int=0)],  # placeholder if not changing
    )

    campaign.title = new_title
    campaign.description = new_description
    campaign.target_count = new_target_count
    campaign.start_date = new_start_date
    campaign.end_date = new_end_date

    if goal_message is not None:
        campaign.goal_message = goal_message
    if target_area is not None:
        campaign.target_area = target_area

    # Update partner clinics if provided
    if partner_clinic_ids is not None:
        await _verify_clinics_exist(db, partner_clinic_ids)

        # Remove existing associations
        for existing in list(campaign.partner_clinics):
            await db.delete(existing)

        # Add new associations
        for clinic_id in partner_clinic_ids:
            junction = CastrationCampaignClinic(
                campaign_id=campaign.id,
                clinic_id=clinic_id,
            )
            db.add(junction)

    await db.flush()
    await db.refresh(campaign)

    logger.info("Updated castration campaign: %s", campaign_id)
    return campaign


async def increment_completed_count(db: AsyncSession, campaign_id: UUID) -> CastrationCampaign:
    """Increment the completed_count for a castration campaign.

    Called when a voucher for castration service is redeemed at a partner clinic.
    """
    campaign = await get_castration_campaign(db, campaign_id)
    campaign.completed_count += 1
    await db.flush()
    await db.refresh(campaign)

    logger.info(
        "Incremented castration campaign %s: %d/%d",
        campaign_id,
        campaign.completed_count,
        campaign.target_count,
    )
    return campaign
