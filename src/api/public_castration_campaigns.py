"""Public endpoints for castration campaign viewing (no auth required).

GET  /public/castration-campaigns              -- list active/completed campaigns
GET  /public/castration-campaigns/{id}         -- get campaign detail with clinics
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.castration_campaign import CastrationCampaign
from src.db.models.vet_clinic import VetClinic
from src.db.session import get_async_session

router = APIRouter(
    prefix="/public/castration-campaigns",
    tags=["public-castration-campaigns"],
)


# --- Response schemas ---


class ClinicPublicResponse(BaseModel):
    """Public-safe clinic information."""

    id: str
    name: str
    city: str
    department: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    class Config:
        from_attributes = True


class CastrationCampaignPublicResponse(BaseModel):
    """Public castration campaign detail."""

    id: str
    title: str
    description: str
    goal_message: str | None = None
    target_count: int
    completed_count: int
    progress_percent: int
    target_area: str
    start_date: str
    end_date: str
    status: str
    partner_clinics: list[ClinicPublicResponse] = Field(default_factory=list)
    created_at: str


class CastrationCampaignListResponse(BaseModel):
    """List of public castration campaigns."""

    items: list[CastrationCampaignPublicResponse]
    total: int


# --- Helpers ---


async def _build_campaign_response(
    db: AsyncSession, campaign: CastrationCampaign
) -> CastrationCampaignPublicResponse:
    """Build public response for a campaign including partner clinics."""
    clinics: list[ClinicPublicResponse] = []
    for junction in campaign.partner_clinics:
        clinic = await db.get(VetClinic, junction.clinic_id)
        if clinic is not None:
            clinics.append(
                ClinicPublicResponse(
                    id=str(clinic.id),
                    name=clinic.name,
                    city=clinic.city,
                    department=clinic.department,
                    latitude=clinic.latitude,
                    longitude=clinic.longitude,
                )
            )

    return CastrationCampaignPublicResponse(
        id=str(campaign.id),
        title=campaign.title,
        description=campaign.description,
        goal_message=campaign.goal_message,
        target_count=campaign.target_count,
        completed_count=campaign.completed_count,
        progress_percent=campaign.progress_percent,
        target_area=campaign.target_area,
        start_date=campaign.start_date.isoformat(),
        end_date=campaign.end_date.isoformat(),
        status=campaign.status,
        partner_clinics=clinics,
        created_at=campaign.created_at.isoformat(),
    )


# --- Endpoints ---


@router.get("", response_model=CastrationCampaignListResponse)
async def list_public_castration_campaigns(
    db: AsyncSession = Depends(get_async_session),
) -> CastrationCampaignListResponse:
    """List castration campaigns visible to the public (active or completed)."""
    today = date.today()
    query = (
        select(CastrationCampaign)
        .where(CastrationCampaign.start_date <= today)
        .order_by(CastrationCampaign.start_date.desc())
    )
    result = await db.execute(query)
    campaigns = list(result.scalars().all())

    items = [await _build_campaign_response(db, c) for c in campaigns]
    return CastrationCampaignListResponse(items=items, total=len(items))


@router.get("/{campaign_id}", response_model=CastrationCampaignPublicResponse)
async def get_public_castration_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> CastrationCampaignPublicResponse:
    """Get a single castration campaign by ID (public)."""
    campaign = await db.get(CastrationCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return await _build_campaign_response(db, campaign)
