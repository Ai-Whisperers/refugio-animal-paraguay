"""Castration campaign impact report API.

Endpoints:
  GET /public/castration-campaigns/{id}/report  - Impact report (public)
  GET /api/castration/campaigns/{id}/report     - Full report (staff)
"""

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.castration_campaign import (
    CastrationCampaign,
    CastrationCampaignClinic,
)
from src.db.models.castration_drive import CastrationDrive
from src.db.models.castration_photo import CastrationPhoto
from src.db.models.user import User
from src.db.models.vet_clinic import VetClinic
from src.db.session import get_db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

admin_router = APIRouter(
    prefix="/api/castration/campaigns",
    tags=["castration-report"],
)

public_router = APIRouter(
    prefix="/public/castration-campaigns",
    tags=["castration-report-public"],
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

MAX_FEATURED_PHOTOS = 6


class ClinicContribution(BaseModel):
    """A partner clinic's contribution to the campaign."""

    clinic_id: UUID
    clinic_name: str
    drives_hosted: int


class DrivesSummary(BaseModel):
    """Summary of castration drives for the campaign."""

    total_drives: int
    completed_drives: int
    total_registered: int
    total_completed: int


class PhotoSummary(BaseModel):
    """Photo gallery summary for the report."""

    total_photos: int
    before_count: int
    after_count: int
    recovery_count: int
    featured_urls: list[str]


class ImpactReportResponse(BaseModel):
    """Full impact report for a castration campaign."""

    campaign_id: UUID
    title: str
    description: str
    target_area: str
    start_date: date
    end_date: date
    status: str
    is_complete: bool

    # By the numbers
    target_count: int
    completed_count: int
    progress_percent: int
    campaign_duration_days: int

    # Partner clinics
    clinics: list[ClinicContribution]
    total_clinics: int

    # Drives
    drives: DrivesSummary

    # Photos
    photos: PhotoSummary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _build_report(campaign_id: UUID, db: AsyncSession) -> ImpactReportResponse:
    """Build a complete impact report for a castration campaign."""
    # Fetch campaign
    result = await db.execute(
        select(CastrationCampaign).where(CastrationCampaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    # Partner clinics with drive counts
    clinic_query = (
        select(
            VetClinic.id,
            VetClinic.name,
            func.count(CastrationDrive.id).label("drives_hosted"),
        )
        .join(
            CastrationCampaignClinic,
            CastrationCampaignClinic.clinic_id == VetClinic.id,
        )
        .outerjoin(
            CastrationDrive,
            (CastrationDrive.clinic_id == VetClinic.id)
            & (CastrationDrive.campaign_id == campaign_id),
        )
        .where(CastrationCampaignClinic.campaign_id == campaign_id)
        .group_by(VetClinic.id, VetClinic.name)
        .order_by(func.count(CastrationDrive.id).desc())
    )
    clinic_rows = (await db.execute(clinic_query)).all()
    clinics = [
        ClinicContribution(
            clinic_id=row.id,
            clinic_name=row.name,
            drives_hosted=row.drives_hosted,
        )
        for row in clinic_rows
    ]

    # Drives summary
    drives_query = select(
        func.count(CastrationDrive.id).label("total"),
        func.count(CastrationDrive.id)
        .filter(CastrationDrive.status == "completed")
        .label("completed"),
        func.coalesce(func.sum(CastrationDrive.registered_count), 0).label("registered"),
        func.coalesce(func.sum(CastrationDrive.completed_count), 0).label("completed_animals"),
    ).where(CastrationDrive.campaign_id == campaign_id)
    drives_row = (await db.execute(drives_query)).one()

    drives_summary = DrivesSummary(
        total_drives=drives_row.total,
        completed_drives=drives_row.completed,
        total_registered=drives_row.registered,
        total_completed=drives_row.completed_animals,
    )

    # Photos summary
    photo_counts_query = select(
        func.count(CastrationPhoto.id).label("total"),
        func.count(CastrationPhoto.id)
        .filter(CastrationPhoto.photo_type == "before")
        .label("before_count"),
        func.count(CastrationPhoto.id)
        .filter(CastrationPhoto.photo_type == "after")
        .label("after_count"),
        func.count(CastrationPhoto.id)
        .filter(CastrationPhoto.photo_type == "recovery")
        .label("recovery_count"),
    ).where(CastrationPhoto.campaign_id == campaign_id)
    photo_row = (await db.execute(photo_counts_query)).one()

    # Featured photos
    featured_query = (
        select(CastrationPhoto.photo_url)
        .where(
            CastrationPhoto.campaign_id == campaign_id,
            CastrationPhoto.public_consent.is_(True),
            CastrationPhoto.is_featured.is_(True),
        )
        .order_by(CastrationPhoto.uploaded_at.desc())
        .limit(MAX_FEATURED_PHOTOS)
    )
    featured_urls = [row[0] for row in (await db.execute(featured_query)).all()]

    photo_summary = PhotoSummary(
        total_photos=photo_row.total,
        before_count=photo_row.before_count,
        after_count=photo_row.after_count,
        recovery_count=photo_row.recovery_count,
        featured_urls=featured_urls,
    )

    # Campaign duration
    duration_days = (campaign.end_date - campaign.start_date).days

    # Determine if campaign is complete
    is_complete = (
        campaign.completed_count >= campaign.target_count or date.today() > campaign.end_date
    )

    return ImpactReportResponse(
        campaign_id=campaign.id,
        title=campaign.title,
        description=campaign.description,
        target_area=campaign.target_area,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        status=campaign.status,
        is_complete=is_complete,
        target_count=campaign.target_count,
        completed_count=campaign.completed_count,
        progress_percent=campaign.progress_percent,
        campaign_duration_days=duration_days,
        clinics=clinics,
        total_clinics=len(clinics),
        drives=drives_summary,
        photos=photo_summary,
    )


# ---------------------------------------------------------------------------
# Public endpoint
# ---------------------------------------------------------------------------


@public_router.get(
    "/{campaign_id}/report",
    response_model=ImpactReportResponse,
    summary="Campaign impact report (public)",
)
async def public_campaign_report(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ImpactReportResponse:
    """Return a public-facing impact report for a castration campaign."""
    return await _build_report(campaign_id, db)


# ---------------------------------------------------------------------------
# Admin endpoint
# ---------------------------------------------------------------------------


@admin_router.get(
    "/{campaign_id}/report",
    response_model=ImpactReportResponse,
    summary="Campaign impact report (staff)",
)
async def admin_campaign_report(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> ImpactReportResponse:
    """Return a full impact report for a castration campaign (staff access)."""
    return await _build_report(campaign_id, db)
