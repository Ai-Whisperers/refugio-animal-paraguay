"""Email campaign scheduling and sending endpoints (staff/admin only).

Endpoints:
  POST   /email-campaigns              — create a new campaign (draft)
  GET    /email-campaigns              — list campaigns
  GET    /email-campaigns/{id}         — get campaign detail
  PATCH  /email-campaigns/{id}         — update a draft campaign
  DELETE /email-campaigns/{id}         — cancel a campaign
  POST   /email-campaigns/{id}/schedule — schedule a draft campaign
  POST   /email-campaigns/{id}/send    — trigger immediate send
  POST   /email-campaigns/{id}/send/ab  — trigger A/B test send
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.email_campaign import EmailCampaign, EmailCampaignStatus
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.email_campaign import (
    EmailCampaignCreate,
    EmailCampaignResponse,
    EmailCampaignSummary,
    EmailCampaignUpdate,
)
from src.schemas.error import RESOURCE_RESPONSES
from src.services.email_ab_test_service import (
    initiate_send_ab,
    is_ab_test_active,
)
from src.services.email_campaign_service import (
    cancel_campaign as cancel_campaign_service,
)
from src.services.email_campaign_service import (
    initiate_send,
)
from src.services.email_campaign_service import (
    schedule_campaign as schedule_campaign_service,
)

router = APIRouter(
    prefix="/email-campaigns",
    tags=["email-campaigns"],
    responses=RESOURCE_RESPONSES,
)


@router.post("", response_model=EmailCampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: EmailCampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> EmailCampaign:
    """Create a new email campaign in draft state. Staff or admin only."""
    campaign = EmailCampaign(
        name=payload.name,
        description=payload.description,
        email_list_id=payload.email_list_id,
        email_template_id=payload.email_template_id,
        scheduled_at=payload.scheduled_at,
        status=EmailCampaignStatus.DRAFT.value,
        created_by_id=current_user.id,
    )
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    return campaign


@router.get("", response_model=list[EmailCampaignSummary])
async def list_campaigns(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> list[EmailCampaign]:
    """List email campaigns. Optionally filter by status."""
    stmt = select(EmailCampaign)
    if status_filter:
        stmt = stmt.where(EmailCampaign.status == status_filter)
    stmt = stmt.order_by(EmailCampaign.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{campaign_id}", response_model=EmailCampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> EmailCampaign:
    """Get email campaign detail."""
    campaign = await db.get(EmailCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email campaign not found",
        )
    return campaign


@router.patch("/{campaign_id}", response_model=EmailCampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    payload: EmailCampaignUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> EmailCampaign:
    """Update a draft campaign. Staff or admin only."""
    campaign = await db.get(EmailCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email campaign not found",
        )
    if campaign.status not in (EmailCampaignStatus.DRAFT, EmailCampaignStatus.SCHEDULED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot update campaign in status '{campaign.status}'",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(campaign, field, value)

    await db.flush()
    await db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> None:
    """Cancel a draft or scheduled campaign."""
    campaign = await db.get(EmailCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email campaign not found",
        )
    try:
        await cancel_campaign_service(db, campaign)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/{campaign_id}/schedule", response_model=EmailCampaignResponse)
async def schedule_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> EmailCampaign:
    """Schedule a draft campaign (requires scheduled_at to be set)."""
    campaign = await db.get(EmailCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email campaign not found",
        )
    try:
        await schedule_campaign_service(db, campaign)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/send", response_model=EmailCampaignResponse)
async def send_campaign_now(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> EmailCampaign:
    """Trigger immediate sending of a draft or scheduled campaign."""
    campaign = await db.get(EmailCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email campaign not found",
        )
    try:
        await initiate_send(db, campaign)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/send/ab", response_model=EmailCampaignResponse)
async def send_campaign_ab(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> EmailCampaign:
    """Trigger A/B subject line test send for a draft or scheduled campaign.

    Requires subject_a and subject_b to be set on the campaign.
    Recipients are split by ab_ratio (default 50/50). Variant attribution
    is tracked on engagement events for stats comparison.
    """
    campaign = await db.get(EmailCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email campaign not found",
        )
    if not is_ab_test_active(campaign):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Campaign does not have an A/B subject line configured. "
            "Set subject_b on the campaign before triggering an A/B send.",
        )
    try:
        await initiate_send_ab(db, campaign)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    await db.refresh(campaign)
    return campaign
