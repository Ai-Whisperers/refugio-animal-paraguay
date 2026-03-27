"""Public (unauthenticated) campaign browsing endpoints.

Endpoints:
  GET /public/campaigns             — list active campaigns with progress
  GET /public/campaigns/{id}        — campaign detail with progress stats
  GET /public/campaigns/{id}/social-proof — social proof metrics + recent donors
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.campaign import Campaign, CampaignDonation, CampaignStatus, FundCategory
from src.db.models.donation import Donation, DonationStatus
from src.db.session import get_db
from src.schemas.campaign import (
    CampaignListResponse,
    CampaignPublicResponse,
    CampaignSocialProofResponse,
)
from src.schemas.error import COMMON_RESPONSES, ErrorResponse
from src.services.campaign_social_proof_service import get_campaign_social_proof

router = APIRouter(
    prefix="/public/campaigns",
    tags=["public-campaigns"],
    responses={
        **COMMON_RESPONSES,
        404: {"description": "Campaign not found", "model": ErrorResponse},
    },
)

DEFAULT_PAGE_SIZE = 12
MAX_PAGE_SIZE = 50


def _compute_days_remaining(deadline: datetime | None) -> int | None:
    """Return whole days until deadline, or None if no deadline is set.

    Returns 0 if the deadline has already passed.
    """
    if deadline is None:
        return None
    now = datetime.now(tz=UTC)
    # Ensure deadline is timezone-aware for comparison
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=UTC)
    delta = deadline - now
    return max(0, delta.days)


def _build_campaign_public_response(
    campaign: Campaign,
    raised_amount_cents: int,
    donation_count: int,
) -> CampaignPublicResponse:
    """Build a public campaign response with computed progress and time fields."""
    progress = (
        min((raised_amount_cents / campaign.target_amount_cents) * 100, 100.0)
        if campaign.target_amount_cents > 0
        else 0.0
    )
    return CampaignPublicResponse(
        id=campaign.id,
        title=campaign.title,
        description=campaign.description,
        impact_story=campaign.impact_story,
        target_amount_cents=campaign.target_amount_cents,
        raised_amount_cents=raised_amount_cents,
        currency=campaign.currency,  # type: ignore[arg-type]
        fund_category=campaign.fund_category,  # type: ignore[arg-type]
        status=campaign.status,  # type: ignore[arg-type]
        featured=campaign.featured,
        image_url=campaign.image_url,
        photo_urls=campaign.photo_urls,
        deadline=campaign.deadline,
        days_remaining=_compute_days_remaining(campaign.deadline),
        min_donation_cents=campaign.min_donation_cents,
        max_donation_cents=campaign.max_donation_cents,
        allow_overfunding=campaign.allow_overfunding,
        donation_count=donation_count,
        progress_percentage=round(progress, 1),
        created_at=campaign.created_at,
    )


@router.get("", response_model=CampaignListResponse)
async def list_active_campaigns(
    category: FundCategory | None = Query(default=None, description="Filter by fund category"),
    featured: bool | None = Query(
        default=None, description="Filter by featured flag (true = featured only)"
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"
    ),
    db: AsyncSession = Depends(get_db),
) -> CampaignListResponse:
    """List active campaigns with progress stats.

    Only campaigns with status='active' are shown publicly.
    Results include computed raised amount, donation count, and days remaining.
    Use ?featured=true to surface featured campaigns prominently.
    """
    base_query = select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE.value)

    if category is not None:
        base_query = base_query.where(Campaign.fund_category == category.value)
    if featured is not None:
        base_query = base_query.where(Campaign.featured == featured)

    # Count total matching campaigns
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch paginated campaigns — featured campaigns sorted first
    offset = (page - 1) * page_size
    data_query = (
        base_query.order_by(Campaign.featured.desc(), Campaign.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(data_query)
    campaigns = list(result.scalars().all())

    # Compute raised amounts for all campaigns
    items = []
    for campaign in campaigns:
        raised_query = (
            select(
                func.coalesce(func.sum(Donation.amount_cents), 0),
                func.count(Donation.id),
            )
            .select_from(CampaignDonation)
            .join(Donation, Donation.id == CampaignDonation.donation_id)
            .where(
                CampaignDonation.campaign_id == campaign.id,
                Donation.status == DonationStatus.COMPLETED.value,
            )
        )
        raised_result = await db.execute(raised_query)
        row = raised_result.one()
        raised_cents = int(row[0])
        count = int(row[1])

        items.append(_build_campaign_public_response(campaign, raised_cents, count))

    return CampaignListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{campaign_id}", response_model=CampaignPublicResponse)
async def get_campaign_detail(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CampaignPublicResponse:
    """Get a single campaign with progress stats.

    Returns 404 if the campaign does not exist or is not active/completed.
    """
    campaign = await db.get(Campaign, campaign_id)

    if campaign is None or campaign.status not in (
        CampaignStatus.ACTIVE.value,
        CampaignStatus.COMPLETED.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    # Compute raised amount and donation count
    raised_query = (
        select(
            func.coalesce(func.sum(Donation.amount_cents), 0),
            func.count(Donation.id),
        )
        .select_from(CampaignDonation)
        .join(Donation, Donation.id == CampaignDonation.donation_id)
        .where(
            CampaignDonation.campaign_id == campaign.id,
            Donation.status == DonationStatus.COMPLETED.value,
        )
    )
    raised_result = await db.execute(raised_query)
    row = raised_result.one()
    raised_cents = int(row[0])
    count = int(row[1])

    return _build_campaign_public_response(campaign, raised_cents, count)


@router.get(
    "/{campaign_id}/social-proof",
    response_model=CampaignSocialProofResponse,
    summary="Campaign social proof: recent donors + momentum metrics",
)
async def get_campaign_social_proof_endpoint(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CampaignSocialProofResponse:
    """Return social proof data for a campaign page.

    Includes:
    - Total raised and donor count
    - Progress percentage (amount raised vs. goal)
    - Momentum metrics: donations in the last 24 hours and 7 days
    - Recent donors list (up to 10) with privacy-respecting display names

    Donors with show_in_public=False are shown as "Anonymous".
    Returns 404 if the campaign does not exist or is not active/completed.
    """
    result = await get_campaign_social_proof(db, campaign_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return result
