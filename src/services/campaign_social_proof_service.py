"""Service for computing campaign social proof metrics.

Computes:
  - Total raised and donor count (existing stats, now grouped per-campaign)
  - Momentum: donations in last 24 hours and last 7 days
  - Recent donors: up to 10 most-recent completed donations, with privacy masking

Privacy rule:
  If donor.show_in_public is False, display_name is "Anonymous" and is_anonymous=True.
  The donation amount and timestamp are always shown (non-sensitive aggregate data).
  Anonymous (donor_id IS NULL) donations are always listed as "Anonymous".
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.campaign import Campaign, CampaignDonation, CampaignStatus
from src.db.models.donation import Donation, DonationStatus, Donor
from src.schemas.campaign import CampaignSocialProofResponse, RecentDonorEntry

logger = logging.getLogger(__name__)

RECENT_DONOR_LIMIT = 10


async def get_campaign_social_proof(
    db: AsyncSession,
    campaign_id: UUID,
) -> CampaignSocialProofResponse | None:
    """Compute social proof metrics for a campaign.

    Returns None if the campaign does not exist or is not active/completed.
    """
    campaign = await db.get(Campaign, campaign_id)
    if campaign is None or campaign.status not in (
        CampaignStatus.ACTIVE.value,
        CampaignStatus.COMPLETED.value,
    ):
        return None

    now = datetime.now(tz=UTC)
    cutoff_24h = now - timedelta(hours=24)
    cutoff_7d = now - timedelta(days=7)

    # --- Totals: raised amount + unique donor count ---
    totals_stmt = (
        select(
            func.coalesce(func.sum(Donation.amount_cents), 0).label("total_cents"),
            func.count(Donation.id).label("donation_count"),
        )
        .select_from(CampaignDonation)
        .join(Donation, Donation.id == CampaignDonation.donation_id)
        .where(
            CampaignDonation.campaign_id == campaign_id,
            Donation.status == DonationStatus.COMPLETED.value,
        )
    )
    totals_row = (await db.execute(totals_stmt)).one()
    total_raised_cents = int(totals_row.total_cents)
    donor_count = int(totals_row.donation_count)

    # --- Momentum: last 24 h ---
    last_24h_stmt = (
        select(func.count(Donation.id))
        .select_from(CampaignDonation)
        .join(Donation, Donation.id == CampaignDonation.donation_id)
        .where(
            CampaignDonation.campaign_id == campaign_id,
            Donation.status == DonationStatus.COMPLETED.value,
            Donation.created_at >= cutoff_24h,
        )
    )
    donations_last_24h = int((await db.execute(last_24h_stmt)).scalar_one())

    # --- Momentum: last 7 d ---
    last_7d_stmt = (
        select(func.count(Donation.id))
        .select_from(CampaignDonation)
        .join(Donation, Donation.id == CampaignDonation.donation_id)
        .where(
            CampaignDonation.campaign_id == campaign_id,
            Donation.status == DonationStatus.COMPLETED.value,
            Donation.created_at >= cutoff_7d,
        )
    )
    donations_last_7d = int((await db.execute(last_7d_stmt)).scalar_one())

    # --- Recent donors: last N completed donations with donor info ---
    recent_stmt = (
        select(Donation, Donor)
        .select_from(CampaignDonation)
        .join(Donation, Donation.id == CampaignDonation.donation_id)
        .outerjoin(Donor, Donor.id == Donation.donor_id)
        .where(
            CampaignDonation.campaign_id == campaign_id,
            Donation.status == DonationStatus.COMPLETED.value,
        )
        .order_by(Donation.created_at.desc())
        .limit(RECENT_DONOR_LIMIT)
    )
    recent_rows = (await db.execute(recent_stmt)).all()

    recent_donors: list[RecentDonorEntry] = []
    for donation, donor in recent_rows:
        is_anonymous = donor is None or not donor.show_in_public
        display_name = "Anonymous" if is_anonymous else donor.full_name.split()[0]

        recent_donors.append(
            RecentDonorEntry(
                display_name=display_name,
                amount_cents=donation.amount_cents,
                currency=donation.currency,  # type: ignore[arg-type]
                donated_at=donation.created_at,
                is_anonymous=is_anonymous,
            )
        )

    # --- Progress percentage ---
    progress_percentage = (
        round(min((total_raised_cents / campaign.target_amount_cents) * 100, 100.0), 1)
        if campaign.target_amount_cents > 0
        else 0.0
    )

    return CampaignSocialProofResponse(
        campaign_id=campaign_id,
        donor_count=donor_count,
        total_raised_cents=total_raised_cents,
        currency=campaign.currency,  # type: ignore[arg-type]
        progress_percentage=progress_percentage,
        donations_last_24_hours=donations_last_24h,
        donations_last_7_days=donations_last_7d,
        recent_donors=recent_donors,
    )
