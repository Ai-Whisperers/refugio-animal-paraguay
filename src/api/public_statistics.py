"""Public statistics endpoint — unauthenticated, cached shelter metrics.

Endpoints:
  GET /api/stats/public  — aggregated shelter statistics (no auth required)
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.services.public_statistics_service import get_public_statistics

router = APIRouter(
    prefix="/api/stats",
    tags=["public-statistics"],
)


class PublicStatisticsResponse(BaseModel):
    """Response schema for public shelter statistics."""

    total_animals_rescued: int = Field(
        ..., description="Total animals ever entered into the shelter"
    )
    total_adopted: int = Field(..., description="Total animals with 'adopted' status")
    total_castrated: int = Field(..., description="Total completed castration surgeries")
    total_donors: int = Field(..., description="Total unique donors with completed donations")
    total_donations_amount_cents: int = Field(
        ..., description="Sum of all completed donations in cents"
    )
    total_volunteers: int = Field(..., description="Total users with volunteer role")
    last_updated: datetime = Field(
        ..., description="When these statistics were last computed (UTC)"
    )

    model_config = {"from_attributes": True}


@router.get(
    "/public",
    response_model=PublicStatisticsResponse,
    summary="Get public shelter statistics",
    description=(
        "Returns aggregated shelter statistics. No authentication required. "
        "Response is cached for 5 minutes."
    ),
)
async def get_public_stats(
    db: AsyncSession = Depends(get_db),
) -> PublicStatisticsResponse:
    """Return cached aggregate statistics about the shelter."""
    try:
        stats = await get_public_statistics(db)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute statistics. Please try again later.",
        ) from None

    return PublicStatisticsResponse(
        total_animals_rescued=stats.total_animals_rescued,
        total_adopted=stats.total_adopted,
        total_castrated=stats.total_castrated,
        total_donors=stats.total_donors,
        total_donations_amount_cents=stats.total_donations_amount_cents,
        total_volunteers=stats.total_volunteers,
        last_updated=stats.last_updated,
    )
