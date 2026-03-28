"""Service integrating castration campaigns with the vet voucher system.

Handles:
- Creating castration vouchers when donations are made to a campaign
- Incrementing campaign completed_count when castration vouchers are redeemed
- Triggering milestone notifications at 25/50/75/100% progress
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.castration_campaign import CastrationCampaignClinic
from src.db.models.vet_voucher import VetVoucher, VoucherStatus
from src.services.castration_campaign_service import (
    get_castration_campaign,
    increment_completed_count,
)

logger = logging.getLogger(__name__)

# Service categories that count as castration
CASTRATION_SERVICE_CATEGORIES = frozenset({"castration_dog", "castration_cat"})

# Milestone thresholds (fractions of target_count)
MILESTONE_THRESHOLDS = (0.25, 0.50, 0.75, 1.0)


class VoucherNotLinkedError(Exception):
    """Raised when a voucher is not linked to a castration campaign."""

    def __init__(self, voucher_id: UUID) -> None:
        self.voucher_id = voucher_id
        self.message = f"Voucher {voucher_id} is not linked to a castration campaign."
        super().__init__(self.message)


def _check_milestone(completed_count: int, target_count: int) -> float | None:
    """Check if a milestone was just crossed.

    Returns the milestone fraction (0.25, 0.50, 0.75, 1.0) if the new
    completed_count crosses a threshold, otherwise None.
    """
    if target_count <= 0:
        return None

    current_pct = completed_count / target_count
    previous_pct = (completed_count - 1) / target_count

    for threshold in MILESTONE_THRESHOLDS:
        if previous_pct < threshold <= current_pct:
            return threshold

    return None


def _milestone_label(threshold: float) -> str:
    """Convert milestone fraction to human-readable label."""
    return f"{int(threshold * 100)}%"


async def get_campaign_partner_clinic_ids(db: AsyncSession, campaign_id: UUID) -> set[UUID]:
    """Get the set of partner clinic IDs for a campaign."""
    query = select(CastrationCampaignClinic.clinic_id).where(
        CastrationCampaignClinic.campaign_id == campaign_id
    )
    result = await db.execute(query)
    return {row[0] for row in result.all()}


async def is_castration_voucher_for_campaign(
    db: AsyncSession,
    voucher: VetVoucher,
    campaign_id: UUID,
) -> bool:
    """Check if a redeemed voucher counts toward a castration campaign.

    True if:
    1. Voucher service_category is a castration type
    2. Voucher was redeemed at a partner clinic of the campaign
    """
    if voucher.service_category not in CASTRATION_SERVICE_CATEGORIES:
        return False

    partner_clinic_ids = await get_campaign_partner_clinic_ids(db, campaign_id)
    return voucher.clinic_id is not None and voucher.clinic_id in partner_clinic_ids


async def handle_voucher_redeemed(
    db: AsyncSession,
    voucher_id: UUID,
    campaign_id: UUID,
) -> dict:
    """Handle a voucher redemption event for a castration campaign.

    1. Verify the voucher is redeemed and counts for the campaign.
    2. Increment campaign completed_count.
    3. Check for milestone and return notification info.

    Returns dict with: campaign_id, completed_count, target_count,
    milestone (if crossed), is_complete.
    """
    voucher = await db.get(VetVoucher, voucher_id)
    if voucher is None:
        raise VoucherNotLinkedError(voucher_id)

    if voucher.status != VoucherStatus.REDEEMED:
        logger.warning(
            "Voucher %s is not redeemed (status=%s), skipping campaign integration",
            voucher_id,
            voucher.status,
        )
        return {"skipped": True, "reason": "voucher_not_redeemed"}

    is_valid = await is_castration_voucher_for_campaign(db, voucher, campaign_id)
    if not is_valid:
        logger.info(
            "Voucher %s does not count for campaign %s (category=%s)",
            voucher_id,
            campaign_id,
            voucher.service_category,
        )
        return {"skipped": True, "reason": "not_applicable"}

    campaign = await increment_completed_count(db, campaign_id)

    milestone = _check_milestone(campaign.completed_count, campaign.target_count)
    is_complete = campaign.completed_count >= campaign.target_count

    logger.info(
        "Campaign %s progress: %d/%d (milestone=%s, complete=%s)",
        campaign_id,
        campaign.completed_count,
        campaign.target_count,
        _milestone_label(milestone) if milestone else "none",
        is_complete,
    )

    result = {
        "skipped": False,
        "campaign_id": str(campaign_id),
        "completed_count": campaign.completed_count,
        "target_count": campaign.target_count,
        "progress_percent": campaign.progress_percent,
        "is_complete": is_complete,
    }

    if milestone is not None:
        result["milestone"] = _milestone_label(milestone)

    return result


async def get_campaign_vouchers(
    db: AsyncSession,
    campaign_id: UUID,
) -> list[VetVoucher]:
    """Get all vouchers linked to partner clinics of a campaign with castration service."""
    partner_clinic_ids = await get_campaign_partner_clinic_ids(db, campaign_id)

    if not partner_clinic_ids:
        return []

    query = (
        select(VetVoucher)
        .where(
            VetVoucher.clinic_id.in_(partner_clinic_ids),
            VetVoucher.service_category.in_(CASTRATION_SERVICE_CATEGORIES),
        )
        .order_by(VetVoucher.purchased_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_campaign_stats(
    db: AsyncSession,
    campaign_id: UUID,
) -> dict:
    """Get detailed stats for a castration campaign including voucher breakdown."""
    campaign = await get_castration_campaign(db, campaign_id)
    partner_clinic_ids = await get_campaign_partner_clinic_ids(db, campaign_id)

    # Count vouchers by status
    voucher_query = select(VetVoucher).where(
        VetVoucher.clinic_id.in_(partner_clinic_ids),
        VetVoucher.service_category.in_(CASTRATION_SERVICE_CATEGORIES),
    )
    result = await db.execute(voucher_query)
    vouchers = list(result.scalars().all())

    status_counts: dict[str, int] = {}
    for v in vouchers:
        status_counts[v.status] = status_counts.get(v.status, 0) + 1

    return {
        "campaign_id": str(campaign_id),
        "title": campaign.title,
        "target_count": campaign.target_count,
        "completed_count": campaign.completed_count,
        "progress_percent": campaign.progress_percent,
        "status": campaign.status,
        "partner_clinic_count": len(partner_clinic_ids),
        "total_vouchers": len(vouchers),
        "vouchers_by_status": status_counts,
    }
