"""Public impact endpoint — unauthenticated, cached monthly statistics.

Endpoints:
  GET /api/stats/impact  — monthly impact data for the last 12 months
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.services.impact_monthly_service import get_impact_summary

router = APIRouter(
    prefix="/api/stats",
    tags=["public-statistics"],
)


class MonthlyImpactItem(BaseModel):
    """One month of impact data."""

    year: int
    month: int
    animals_rescued: int
    adoptions_completed: int
    castrations_performed: int
    donations_total_cents: int

    model_config = {"from_attributes": True}


class ImpactResponse(BaseModel):
    """Response for the public impact page."""

    total_animals_rescued: int = Field(..., description="All-time animals entered")
    total_adopted: int = Field(..., description="All-time completed adoptions")
    total_castrated: int = Field(..., description="All-time completed castrations")
    total_donations_cents: int = Field(..., description="All-time donation sum (cents)")
    months: list[MonthlyImpactItem] = Field(..., description="Monthly breakdown for last 12 months")
    last_updated: datetime

    model_config = {"from_attributes": True}


@router.get(
    "/impact",
    response_model=ImpactResponse,
    summary="Get public impact statistics (monthly)",
    description=(
        "Returns all-time totals and monthly aggregates for the last 12 months. "
        "No authentication required. Response is cached for 1 hour."
    ),
)
async def get_impact_stats(
    db: AsyncSession = Depends(get_db),
) -> ImpactResponse:
    """Return cached monthly impact statistics."""
    try:
        summary = await get_impact_summary(db)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute impact statistics. Please try again later.",
        ) from None

    return ImpactResponse(
        total_animals_rescued=summary.total_animals_rescued,
        total_adopted=summary.total_adopted,
        total_castrated=summary.total_castrated,
        total_donations_cents=summary.total_donations_cents,
        months=[
            MonthlyImpactItem(
                year=m.year,
                month=m.month,
                animals_rescued=m.animals_rescued,
                adoptions_completed=m.adoptions_completed,
                castrations_performed=m.castrations_performed,
                donations_total_cents=m.donations_total_cents,
            )
            for m in summary.months
        ],
        last_updated=summary.last_updated,
    )
