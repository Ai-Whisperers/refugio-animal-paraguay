"""Rescuer campaign management API.

Allows authenticated rescuers to create and manage fundraising campaigns.
Provides both a portal interface for rescuers and a public campaign detail endpoint.

Endpoints:
    GET    /api/portal/rescuer/campaigns           -- list rescuer's campaigns
    POST   /api/portal/rescuer/campaigns           -- create a campaign
    GET    /api/portal/rescuer/campaigns/{id}      -- get campaign detail
    PATCH  /api/portal/rescuer/campaigns/{id}/status -- end/archive campaign
    GET    /api/rescuers/{slug}/campaigns/{id}     -- public campaign detail
"""

import logging
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user
from src.db.models.user import User
from src.db.session import get_db
from src.services.rescuer_campaign_service import (
    RescuerCampaignNotFoundError,
    RescuerCampaignPermissionError,
    RescuerNotFoundError,
    create_rescuer_campaign,
    end_rescuer_campaign,
    get_public_campaign_detail,
    get_rescuer_campaign,
    list_rescuer_campaigns,
)

logger = logging.getLogger(__name__)

portal_router = APIRouter(
    prefix="/api/portal/rescuer/campaigns",
    tags=["rescuer-campaigns-portal"],
)

public_router = APIRouter(
    prefix="/api/rescuers",
    tags=["rescuer-campaigns-public"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50
MAX_TARGET_AMOUNT_EUR = 50_000
MIN_TARGET_AMOUNT_EUR = 10


class CampaignStatus(StrEnum):
    """Rescuer campaign lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class FundCategory(StrEnum):
    """Campaign fund category."""

    MEDICAL = "medical"
    FOOD = "food"
    OPERATIONS = "operations"
    RESCUE = "rescue"
    GENERAL = "general"


VALID_END_TRANSITIONS: set[str] = {"active", "draft"}

STATUS_LABELS_ES: dict[str, str] = {
    "draft": "Borrador",
    "active": "Activa",
    "completed": "Completada",
    "archived": "Archivada",
}

CATEGORY_LABELS_ES: dict[str, str] = {
    "medical": "Medico",
    "food": "Alimento",
    "operations": "Operaciones",
    "rescue": "Rescate",
    "general": "General",
}


def _category_label(key: str) -> str:
    return CATEGORY_LABELS_ES.get(key, key)


def _status_label(key: str) -> str:
    return STATUS_LABELS_ES.get(key, key)


# ---------------------------------------------------------------------------
# Schemas — Portal
# ---------------------------------------------------------------------------


class CampaignCreateRequest(BaseModel):
    """Request body to create a rescuer campaign."""

    title: str = Field(..., min_length=5, max_length=200, description="Campaign title")
    description: str = Field(
        ..., min_length=20, max_length=2000, description="Campaign description"
    )
    target_amount_eur: float = Field(
        ...,
        ge=MIN_TARGET_AMOUNT_EUR,
        le=MAX_TARGET_AMOUNT_EUR,
        description="Fundraising target in EUR",
    )
    fund_category: FundCategory = Field(
        default=FundCategory.RESCUE, description="Category of funds raised"
    )
    goal_message: str | None = Field(
        default=None, max_length=300, description="Short motivational message"
    )
    animal_ids: list[UUID] = Field(
        default_factory=list, max_length=20, description="Animal UUIDs involved"
    )
    photo_urls: list[str] = Field(
        default_factory=list, max_length=5, description="Photo URLs for campaign"
    )
    deadline: datetime | None = Field(
        default=None, description="Optional campaign deadline (ISO 8601)"
    )


class CampaignStatusPatchRequest(BaseModel):
    """Request to end or archive a campaign."""

    action: str = Field(..., description="Action to perform: 'complete' or 'archive'")
    impact_message: str | None = Field(
        default=None, max_length=500, description="Impact message sent to donors on completion"
    )


class CampaignResponse(BaseModel):
    """Response schema for a rescuer campaign."""

    id: UUID
    title: str
    description: str
    target_amount_eur: float
    raised_amount_eur: float
    donor_count: int
    fund_category: str
    category_label_es: str
    status: str
    status_label_es: str
    goal_message: str | None
    animal_ids: list[UUID]
    photo_urls: list[str]
    deadline: datetime | None
    requires_approval: bool
    created_at: datetime
    updated_at: datetime


class CampaignListResponse(BaseModel):
    """Paginated list of rescuer campaigns."""

    campaigns: list[CampaignResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Schemas — Public
# ---------------------------------------------------------------------------


class PublicCampaignDonorEntry(BaseModel):
    """A single donor entry shown on the campaign page."""

    donor_name: str
    amount_eur: float
    donated_at: str


class PublicCampaignDetailResponse(BaseModel):
    """Public campaign detail with progress and donor list."""

    id: UUID
    rescuer_slug: str
    rescuer_name: str
    rescuer_verified: bool
    title: str
    description: str
    target_amount_eur: float
    raised_amount_eur: float
    progress_pct: float
    donor_count: int
    fund_category: str
    category_label_es: str
    status: str
    status_label_es: str
    goal_message: str | None
    photo_urls: list[str]
    deadline: datetime | None
    recent_donors: list[PublicCampaignDonorEntry]
    created_at: datetime


# ---------------------------------------------------------------------------
# Portal endpoints
# ---------------------------------------------------------------------------


@portal_router.get(
    "",
    response_model=CampaignListResponse,
    summary="List rescuer's campaigns",
)
async def list_my_campaigns(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CampaignListResponse:
    """Return paginated list of campaigns created by the authenticated rescuer."""
    try:
        result = await list_rescuer_campaigns(
            user_id=current_user.id,
            page=page,
            page_size=page_size,
            db=db,
        )
    except RescuerNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "RESCUER_PROFILE_NOT_FOUND",
                "message": "No rescuer profile found for this user.",
            },
        ) from err

    campaigns = [
        CampaignResponse(
            **c,
            category_label_es=_category_label(str(c["fund_category"])),
            status_label_es=_status_label(str(c["status"])),
        )
        for c in result["campaigns"]
    ]
    return CampaignListResponse(
        campaigns=campaigns,
        total=result["total"],
        page=page,
        page_size=page_size,
    )


@portal_router.post(
    "",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a rescuer campaign",
)
async def create_campaign(
    body: CampaignCreateRequest,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """Create a fundraising campaign for the authenticated rescuer.

    Verified rescuers receive immediate activation (status=active).
    Unverified rescuers create a draft pending admin approval.
    """
    try:
        campaign = await create_rescuer_campaign(
            user_id=current_user.id,
            title=body.title,
            description=body.description,
            target_amount_eur=body.target_amount_eur,
            fund_category=body.fund_category.value,
            goal_message=body.goal_message,
            animal_ids=[str(aid) for aid in body.animal_ids],
            photo_urls=body.photo_urls,
            deadline=body.deadline,
            db=db,
        )
    except RescuerNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "RESCUER_PROFILE_REQUIRED",
                "message": "Register as a rescuer before creating campaigns.",
            },
        ) from err

    return CampaignResponse(
        **campaign,
        category_label_es=_category_label(str(campaign["fund_category"])),
        status_label_es=_status_label(str(campaign["status"])),
    )


@portal_router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Get rescuer campaign detail",
)
async def get_my_campaign(
    campaign_id: UUID,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """Return a single campaign owned by the authenticated rescuer."""
    try:
        campaign = await get_rescuer_campaign(
            user_id=current_user.id,
            campaign_id=campaign_id,
            db=db,
        )
    except RescuerNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"code": "RESCUER_NOT_FOUND"}
        ) from err
    except RescuerCampaignNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": "Campaign not found."},
        ) from err
    except RescuerCampaignPermissionError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "CAMPAIGN_FORBIDDEN", "message": "You do not own this campaign."},
        ) from err

    return CampaignResponse(
        **campaign,
        category_label_es=_category_label(str(campaign["fund_category"])),
        status_label_es=_status_label(str(campaign["status"])),
    )


@portal_router.patch(
    "/{campaign_id}/status",
    response_model=CampaignResponse,
    summary="End or archive a rescuer campaign",
)
async def update_campaign_status(
    campaign_id: UUID,
    body: CampaignStatusPatchRequest,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """Complete or archive a campaign owned by the authenticated rescuer.

    Completing sends an impact notification to donors (if impact_message provided).
    """
    if body.action not in ("complete", "archive"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_ACTION", "message": "action must be 'complete' or 'archive'."},
        )

    try:
        campaign = await end_rescuer_campaign(
            user_id=current_user.id,
            campaign_id=campaign_id,
            action=body.action,
            impact_message=body.impact_message,
            db=db,
        )
    except RescuerNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"code": "RESCUER_NOT_FOUND"}
        ) from err
    except RescuerCampaignNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAMPAIGN_NOT_FOUND"},
        ) from err
    except RescuerCampaignPermissionError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "CAMPAIGN_FORBIDDEN"},
        ) from err

    return CampaignResponse(
        **campaign,
        category_label_es=_category_label(str(campaign["fund_category"])),
        status_label_es=_status_label(str(campaign["status"])),
    )


# ---------------------------------------------------------------------------
# Public endpoint
# ---------------------------------------------------------------------------


@public_router.get(
    "/{slug}/campaigns/{campaign_id}",
    response_model=PublicCampaignDetailResponse,
    summary="Public rescuer campaign detail",
)
async def get_public_campaign(
    slug: str,
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PublicCampaignDetailResponse:
    """Return public campaign detail including progress bar and recent donors."""
    try:
        detail = await get_public_campaign_detail(
            rescuer_slug=slug,
            campaign_id=campaign_id,
            db=db,
        )
    except RescuerNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESCUER_NOT_FOUND", "message": f"Rescuer '{slug}' not found."},
        ) from err
    except RescuerCampaignNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAMPAIGN_NOT_FOUND", "message": "Campaign not found."},
        ) from err

    return PublicCampaignDetailResponse(
        **detail,
        category_label_es=_category_label(str(detail["fund_category"])),
        status_label_es=_status_label(str(detail["status"])),
    )
