"""Public donor leaderboard API endpoint.

Endpoints:
  GET /public/leaderboard/donors  - Top donors by total donation amount
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import Donation, Donor
from src.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/public/leaderboard",
    tags=["leaderboard"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPLETED_STATUS = "completed"
DEFAULT_LIMIT = 20
MAX_LIMIT = 100
ANONYMOUS_DISPLAY_NAME = "Donante anonimo"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class LeaderboardEntry(BaseModel):
    """A single donor entry in the leaderboard."""

    rank: int
    donor_id: str | None
    display_name: str
    country: str | None
    total_donated_cents: int
    currency: str
    donation_count: int
    is_anonymous: bool


class LeaderboardResponse(BaseModel):
    """Paginated leaderboard response."""

    items: list[LeaderboardEntry]
    total_donors: int
    total_raised_cents: int
    currency: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/donors",
    response_model=LeaderboardResponse,
    summary="Top donors leaderboard",
)
async def get_donor_leaderboard(
    currency: str = Query("EUR", pattern="^(EUR|PYG|USD)$"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
    campaign_id: UUID | None = Query(None, description="Filter by campaign"),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardResponse:
    """Return top donors ranked by total donation amount.

    Only includes donors with show_in_public=True and completed donations.
    Anonymous donations (no donor_id) are excluded from the leaderboard.
    Optionally filter by campaign using target_type + target_id.
    """
    # Base query: join donors with their completed donations
    base_filter = [
        Donation.status == COMPLETED_STATUS,
        Donation.currency == currency,
        Donation.donor_id.isnot(None),
        Donor.show_in_public.is_(True),
    ]

    if campaign_id:
        base_filter.extend(
            [
                Donation.target_type == "campaign",
                Donation.target_id == campaign_id,
            ]
        )

    # Aggregate query for individual donors
    donor_query = (
        select(
            Donor.id,
            Donor.full_name,
            Donor.country,
            func.sum(Donation.amount_cents).label("total_cents"),
            func.count(Donation.id).label("donation_count"),
        )
        .join(Donor, Donation.donor_id == Donor.id)
        .where(*base_filter)
        .group_by(Donor.id, Donor.full_name, Donor.country)
        .order_by(func.sum(Donation.amount_cents).desc())
    )

    # Count total qualifying donors
    count_subq = donor_query.subquery()
    count_result = await db.execute(select(func.count()).select_from(count_subq))
    total_donors = count_result.scalar() or 0

    # Total raised across all qualifying donations
    total_query = (
        select(func.coalesce(func.sum(Donation.amount_cents), 0))
        .join(Donor, Donation.donor_id == Donor.id)
        .where(*base_filter)
    )
    total_result = await db.execute(total_query)
    total_raised_cents = total_result.scalar() or 0

    # Paginated donor list
    rows_result = await db.execute(donor_query.offset(offset).limit(limit))
    rows = rows_result.all()

    items = [
        LeaderboardEntry(
            rank=offset + idx + 1,
            donor_id=str(row.id),
            display_name=_mask_name(row.full_name),
            country=row.country,
            total_donated_cents=row.total_cents,
            currency=currency,
            donation_count=row.donation_count,
            is_anonymous=False,
        )
        for idx, row in enumerate(rows)
    ]

    return LeaderboardResponse(
        items=items,
        total_donors=total_donors,
        total_raised_cents=total_raised_cents,
        currency=currency,
    )


def _mask_name(full_name: str) -> str:
    """Show first name + last initial for privacy.

    'Juan Carlos Perez' -> 'Juan Carlos P.'
    'Ana' -> 'Ana'
    """
    parts = full_name.strip().split()
    if len(parts) <= 1:
        return full_name
    return " ".join(parts[:-1]) + " " + parts[-1][0] + "."
