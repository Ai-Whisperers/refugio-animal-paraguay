"""Admin endpoints for castration campaign management.

Endpoints:
    POST   /admin/campaigns/castration           -- create castration campaign
    GET    /admin/campaigns/castration           -- list all castration campaigns
    GET    /admin/campaigns/castration/{id}      -- get campaign details
    PUT    /admin/campaigns/castration/{id}      -- update campaign
"""

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.services.castration_campaign_service import (
    CampaignNotFoundError,
    ClinicNotFoundError,
    InvalidCampaignError,
    create_castration_campaign,
    get_castration_campaign,
    list_castration_campaigns,
    update_castration_campaign,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/campaigns/castration",
    tags=["castration-campaigns"],
    responses=RESOURCE_RESPONSES,
)


# --- Schemas ---


class CreateCastrationCampaignRequest(BaseModel):
    """Request body for creating a castration campaign."""

    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    target_count: int = Field(..., gt=0)
    target_area: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date
    partner_clinic_ids: list[UUID] = Field(..., min_length=1)
    goal_message: str | None = None


class UpdateCastrationCampaignRequest(BaseModel):
    """Request body for updating a castration campaign."""

    title: str | None = Field(None, min_length=5, max_length=200)
    description: str | None = Field(None, min_length=10, max_length=1000)
    target_count: int | None = Field(None, gt=0)
    target_area: str | None = Field(None, min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    partner_clinic_ids: list[UUID] | None = None
    goal_message: str | None = None


class PartnerClinicSchema(BaseModel):
    """Partner clinic in a castration campaign."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    created_at: str


class CastrationCampaignResponse(BaseModel):
    """Single castration campaign response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    goal_message: str | None = None
    target_count: int
    completed_count: int
    target_area: str
    start_date: date
    end_date: date
    status: str
    progress_percent: int
    created_at: str
    updated_at: str
    partner_clinics: list[PartnerClinicSchema] = []


class CastrationCampaignListResponse(BaseModel):
    """List of castration campaigns."""

    items: list[CastrationCampaignResponse]
    total: int


# --- Endpoints ---


@router.post(
    "",
    response_model=CastrationCampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign(
    body: CreateCastrationCampaignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> CastrationCampaignResponse:
    """Create a new castration campaign."""
    try:
        campaign = await create_castration_campaign(
            db,
            title=body.title,
            description=body.description,
            target_count=body.target_count,
            target_area=body.target_area,
            start_date=body.start_date,
            end_date=body.end_date,
            partner_clinic_ids=body.partner_clinic_ids,
            goal_message=body.goal_message,
            created_by_id=current_user.id,
        )
    except InvalidCampaignError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from None
    except ClinicNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from None

    await db.commit()
    return CastrationCampaignResponse.model_validate(campaign)


@router.get(
    "",
    response_model=CastrationCampaignListResponse,
)
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> CastrationCampaignListResponse:
    """List all castration campaigns."""
    campaigns = await list_castration_campaigns(db)
    return CastrationCampaignListResponse(
        items=[CastrationCampaignResponse.model_validate(c) for c in campaigns],
        total=len(campaigns),
    )


@router.get(
    "/{campaign_id}",
    response_model=CastrationCampaignResponse,
)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> CastrationCampaignResponse:
    """Get detailed view of a castration campaign."""
    try:
        campaign = await get_castration_campaign(db, campaign_id)
    except CampaignNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Castration campaign {campaign_id} not found.",
        ) from None

    return CastrationCampaignResponse.model_validate(campaign)


@router.put(
    "/{campaign_id}",
    response_model=CastrationCampaignResponse,
)
async def update_campaign(
    campaign_id: UUID,
    body: UpdateCastrationCampaignRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> CastrationCampaignResponse:
    """Update a castration campaign's details.

    completed_count is read-only and cannot be changed through this endpoint.
    """
    try:
        campaign = await update_castration_campaign(
            db,
            campaign_id,
            title=body.title,
            description=body.description,
            goal_message=body.goal_message,
            target_count=body.target_count,
            target_area=body.target_area,
            start_date=body.start_date,
            end_date=body.end_date,
            partner_clinic_ids=body.partner_clinic_ids,
        )
    except CampaignNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Castration campaign {campaign_id} not found.",
        ) from None
    except InvalidCampaignError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from None
    except ClinicNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from None

    await db.commit()
    return CastrationCampaignResponse.model_validate(campaign)
