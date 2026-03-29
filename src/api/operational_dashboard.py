"""Operational dashboard API endpoint (RAP-250).

Provides live shelter metrics aggregated from the database. Intended for
staff/admin use to monitor day-to-day shelter operations.

Endpoints:
  GET /api/admin/operational-dashboard/metrics  — aggregated operational KPIs
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.operational_metrics_service import (
    DEFAULT_SHELTER_CAPACITY,
    get_operational_metrics,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/operational-dashboard",
    tags=["operational-dashboard"],
)

# ---------------------------------------------------------------------------
# Query parameter bounds
# ---------------------------------------------------------------------------

MIN_PERIOD_DAYS = 1
MAX_PERIOD_DAYS = 365
DEFAULT_PERIOD_DAYS = 30

MIN_CAPACITY = 1
MAX_CAPACITY = 10000

# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class PopulationBreakdownSchema(BaseModel):
    intake: int
    quarantine: int
    available: int
    foster: int
    under_treatment: int
    adopted: int
    deceased: int
    total: int


class OccupancySchema(BaseModel):
    current_count: int
    capacity: int
    occupancy_rate_pct: float


class PeriodCountsSchema(BaseModel):
    period_days: int
    intake_count: int
    outcome_count: int


class SpeciesBreakdownSchema(BaseModel):
    dog: int
    cat: int
    other: int


class OperationalMetricsResponse(BaseModel):
    generated_at: str
    population: PopulationBreakdownSchema
    occupancy: OccupancySchema
    period: PeriodCountsSchema
    species: SpeciesBreakdownSchema
    avg_los_days: float


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/metrics", response_model=OperationalMetricsResponse, summary="Aggregated operational metrics"
)
async def get_metrics(
    period_days: Annotated[
        int,
        Query(
            ge=MIN_PERIOD_DAYS,
            le=MAX_PERIOD_DAYS,
            description="Lookback window in days for intake/outcome counts (default: 30)",
        ),
    ] = DEFAULT_PERIOD_DAYS,
    capacity: Annotated[
        int,
        Query(
            ge=MIN_CAPACITY,
            le=MAX_CAPACITY,
            description="Shelter capacity override for occupancy calculations (default: 200)",
        ),
    ] = DEFAULT_SHELTER_CAPACITY,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> OperationalMetricsResponse:
    """Return live aggregated operational metrics for shelter staff.

    All values are computed from live database queries. Response includes:

    - **population**: current animal counts grouped by status
    - **occupancy**: current animals vs. shelter capacity
    - **period**: intake and outcome counts for the specified window
    - **species**: breakdown of sheltered animals by species
    - **avg_los_days**: average length of stay for in-facility animals

    Auth: requires staff or admin role.
    """
    metrics = await get_operational_metrics(db, period_days=period_days, capacity=capacity)

    return OperationalMetricsResponse(
        generated_at=metrics.generated_at,
        population=PopulationBreakdownSchema(
            intake=metrics.population.intake,
            quarantine=metrics.population.quarantine,
            available=metrics.population.available,
            foster=metrics.population.foster,
            under_treatment=metrics.population.under_treatment,
            adopted=metrics.population.adopted,
            deceased=metrics.population.deceased,
            total=metrics.population.total,
        ),
        occupancy=OccupancySchema(
            current_count=metrics.occupancy.current_count,
            capacity=metrics.occupancy.capacity,
            occupancy_rate_pct=metrics.occupancy.occupancy_rate_pct,
        ),
        period=PeriodCountsSchema(
            period_days=metrics.period.period_days,
            intake_count=metrics.period.intake_count,
            outcome_count=metrics.period.outcome_count,
        ),
        species=SpeciesBreakdownSchema(
            dog=metrics.species.dog,
            cat=metrics.species.cat,
            other=metrics.species.other,
        ),
        avg_los_days=metrics.avg_los_days,
    )
