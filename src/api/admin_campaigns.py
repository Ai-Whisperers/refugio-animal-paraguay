"""Admin campaign management endpoints (staff/admin only).

Endpoints:
  POST  /admin/campaigns             — create a new campaign
  PATCH /admin/campaigns/{id}        — update an existing campaign
  GET   /admin/campaigns             — list all campaigns (any status)
  GET   /admin/campaigns/{id}        — get campaign detail
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.campaign import Campaign, CampaignStatus
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.campaign import (
    CampaignCreate,
    CampaignResponse,
    CampaignUpdate,
)

router = APIRouter(prefix="/admin/campaigns", tags=["admin-campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> Campaign:
    """Create a new fundraising campaign. Staff or admin only."""
    campaign = Campaign(
        title=payload.title,
        description=payload.description,
        impact_story=payload.impact_story,
        target_amount_cents=payload.target_amount_cents,
        currency=payload.currency.value,
        fund_category=payload.fund_category.value,
        featured=payload.featured,
        image_url=payload.image_url,
        photo_urls=payload.photo_urls,
        deadline=payload.deadline,
        min_donation_cents=payload.min_donation_cents,
        max_donation_cents=payload.max_donation_cents,
        allow_overfunding=payload.allow_overfunding,
        created_by_id=current_user.id,
    )
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    return campaign


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    payload: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> Campaign:
    """Update an existing campaign. Staff or admin only."""
    campaign = await db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(value, "value"):
            # Convert enum to string value for DB storage
            value = value.value
        setattr(campaign, field, value)

    await db.flush()
    await db.refresh(campaign)
    return campaign


@router.get("", response_model=list[CampaignResponse])
async def list_all_campaigns(
    campaign_status: CampaignStatus | None = Query(default=None, alias="status"),
    featured: bool | None = Query(default=None, description="Filter by featured flag"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> list[Campaign]:
    """List all campaigns with optional status and featured filters. Staff or admin only."""
    stmt = select(Campaign)
    if campaign_status is not None:
        stmt = stmt.where(Campaign.status == campaign_status.value)
    if featured is not None:
        stmt = stmt.where(Campaign.featured == featured)
    stmt = stmt.order_by(Campaign.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> Campaign:
    """Get a single campaign by ID. Staff or admin only."""
    campaign = await db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign
