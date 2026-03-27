"""Portal API endpoints for authenticated public users.

Endpoints:
  GET /api/portal/dashboard  - Unified personal dashboard data
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.dashboard import (
    ApplicationItem,
    DashboardResponse,
    DonationStats,
    SponsoredAnimalItem,
)
from src.schemas.error import COMMON_RESPONSES
from src.services.dashboard_service import get_dashboard_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portal", tags=["portal"], responses=COMMON_RESPONSES)


@router.get("/dashboard", response_model=DashboardResponse)
async def portal_dashboard(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """Return aggregated dashboard data for the authenticated user.

    Includes adoption applications, donation summary, and sponsored animals.
    Sections are populated based on data availability (matched by email).
    """
    data = await get_dashboard_data(db, user)

    return DashboardResponse(
        user_id=data.user_id,
        display_name=data.display_name,
        email=data.email,
        role=data.role,
        applications=[
            ApplicationItem(
                id=app.id,
                animal_name=app.animal_name,
                animal_species=app.animal_species,
                submitted_at=app.submitted_at,
                status=app.status,
            )
            for app in data.applications
        ],
        donation_summary=DonationStats(
            total_count=data.donation_summary.total_count,
            total_amount_cents=data.donation_summary.total_amount_cents,
            currency=data.donation_summary.currency,
            last_donation_at=data.donation_summary.last_donation_at,
        ),
        sponsored_animals=[
            SponsoredAnimalItem(
                animal_id=sa.animal_id,
                animal_name=sa.animal_name,
                animal_species=sa.animal_species,
                tier_name=sa.tier_name,
                frequency=sa.frequency,
                status=sa.status,
            )
            for sa in data.sponsored_animals
        ],
        total_applications=len(data.applications),
        total_sponsored_animals=len(data.sponsored_animals),
    )
