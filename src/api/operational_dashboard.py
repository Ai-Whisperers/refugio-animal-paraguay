"""Operational dashboard API endpoints (RAP-250, RAP-252).

Provides live shelter metrics aggregated from the database. Intended for
staff/admin use to monitor day-to-day shelter operations.

Endpoints:
  GET /api/admin/operational-dashboard/metrics  — aggregated operational KPIs
  GET /api/admin/operational-dashboard/trends   — time-series intake/outcome trends
"""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.operational_metrics_service import (
    DEFAULT_SHELTER_CAPACITY,
    get_operational_metrics,
    get_trend_data,
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


# ---------------------------------------------------------------------------
# Trends endpoint (RAP-252)
# ---------------------------------------------------------------------------

# Query parameter bounds for lookback window.
MAX_TREND_LOOKBACK_DAYS = 730


class TrendDataPointSchema(BaseModel):
    period_label: str
    intake_count: int
    outcome_count: int


class TrendsResponse(BaseModel):
    interval: str
    lookback_days: int
    generated_at: str
    data_points: list[TrendDataPointSchema]


@router.get(
    "/trends",
    response_model=TrendsResponse,
    summary="Time-series intake/outcome trend data",
)
async def get_trends(
    interval: Annotated[
        Literal["daily", "weekly", "monthly"],
        Query(description="Grouping interval: daily, weekly, or monthly (default: monthly)"),
    ] = "monthly",
    lookback_days: Annotated[
        int,
        Query(
            ge=1,
            le=MAX_TREND_LOOKBACK_DAYS,
            description=(
                "Days of history to include. Defaults: daily=30, weekly=90, monthly=365."
            ),
        ),
    ] = 0,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> TrendsResponse:
    """Return time-series intake and outcome trend data grouped by interval.

    Each data point represents one period (day/week/month) with:
    - **period_label**: Human-readable label (e.g. "29/03", "Sem 13", "Mar 2026")
    - **intake_count**: Animals that entered the shelter in this period
    - **outcome_count**: Animals that were adopted in this period (proxy metric)

    Defaults (when lookback_days=0): daily=30d, weekly=90d, monthly=365d.

    Auth: requires staff or admin role.
    """
    resolved_lookback = lookback_days if lookback_days > 0 else None
    trend = await get_trend_data(db, interval=interval, lookback_days=resolved_lookback)

    return TrendsResponse(
        interval=trend.interval,
        lookback_days=trend.lookback_days,
        generated_at=trend.generated_at,
        data_points=[
            TrendDataPointSchema(
                period_label=dp.period_label,
                intake_count=dp.intake_count,
                outcome_count=dp.outcome_count,
            )
            for dp in trend.data_points
        ],
    )
