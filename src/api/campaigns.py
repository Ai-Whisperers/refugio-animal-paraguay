"""Campaign API endpoints.

Manages fundraising campaigns with goals, deadlines, and progress tracking.

Endpoints:
  POST   /campaigns           -- create a new campaign
  GET    /campaigns           -- list campaigns (with filters)
  GET    /campaigns/{id}      -- get campaign detail with progress
  PATCH  /campaigns/{id}      -- update campaign fields/status
  DELETE /campaigns/{id}      -- delete draft campaign
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.campaign import (
    CampaignCreateRequest,
    CampaignListResponse,
    CampaignResponse,
    CampaignUpdateRequest,
)
from src.services.campaign_service import (
    create_campaign,
    delete_campaign,
    get_campaign,
    get_campaign_progress,
    list_campaigns,
    update_campaign,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _enrich_response(campaign: object, progress: dict[str, int]) -> CampaignResponse:
    """Build CampaignResponse with computed progress fields."""
    resp = CampaignResponse.model_validate(campaign)
    resp.raised_amount_cents = progress["raised_amount_cents"]
    resp.donor_count = progress["donor_count"]
    if resp.goal_amount_cents > 0:
        resp.progress_pct = round((resp.raised_amount_cents / resp.goal_amount_cents) * 100, 2)
    return resp


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign_endpoint(
    payload: CampaignCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> CampaignResponse:
    """Create a new fundraising campaign."""
    campaign = await create_campaign(
        db=db,
        title=payload.title,
        description=payload.description,
        goal_amount_cents=payload.goal_amount_cents,
        currency=payload.currency,
        category=payload.category,
        deadline=payload.deadline,
        featured=payload.featured,
        created_by_user_id=current_user.id,
    )
    progress = await get_campaign_progress(db, campaign.id)
    return _enrich_response(campaign, progress)


@router.get(
    "",
    response_model=CampaignListResponse,
)
async def list_campaigns_endpoint(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
    status_filter: str | None = Query(default=None, alias="status"),
    featured_only: bool = Query(default=False),
) -> CampaignListResponse:
    """List campaigns with optional status and featured filters."""
    campaigns = await list_campaigns(db, status_filter=status_filter, featured_only=featured_only)

    items = []
    for c in campaigns:
        progress = await get_campaign_progress(db, c.id)
        items.append(_enrich_response(c, progress))

    return CampaignListResponse(items=items, count=len(items))


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
)
async def get_campaign_endpoint(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> CampaignResponse:
    """Get campaign detail with progress."""
    campaign = await get_campaign(db, campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    progress = await get_campaign_progress(db, campaign.id)
    return _enrich_response(campaign, progress)


@router.patch(
    "/{campaign_id}",
    response_model=CampaignResponse,
)
async def update_campaign_endpoint(
    campaign_id: UUID,
    payload: CampaignUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> CampaignResponse:
    """Update campaign fields or status."""
    campaign = await update_campaign(
        db=db,
        campaign_id=campaign_id,
        title=payload.title,
        description=payload.description,
        goal_amount_cents=payload.goal_amount_cents,
        category=payload.category,
        status=payload.status,
        deadline=payload.deadline,
        featured=payload.featured,
    )
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    progress = await get_campaign_progress(db, campaign.id)
    return _enrich_response(campaign, progress)


@router.delete(
    "/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_campaign_endpoint(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> None:
    """Delete a draft campaign."""
    deleted = await delete_campaign(db, campaign_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found or not in draft status",
        )
