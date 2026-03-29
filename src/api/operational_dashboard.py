"""Operational dashboard API endpoints (RAP-250, RAP-252, RAP-253, RAP-254).

Provides live shelter metrics aggregated from the database. Intended for
staff/admin use to monitor day-to-day shelter operations.

Endpoints:
  GET /api/admin/operational-dashboard/metrics           — aggregated operational KPIs
  GET /api/admin/operational-dashboard/trends            — time-series intake/outcome trends
  GET /api/admin/operational-dashboard/alerts            — capacity alerts and threshold evaluation
  GET /api/admin/operational-dashboard/export/metrics    — CSV export of full metrics snapshot
  GET /api/admin/operational-dashboard/export/population — CSV export of population breakdown
"""

import csv
import io
import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.operational_metrics_service import (
    DEFAULT_CRITICAL_THRESHOLD_PCT,
    DEFAULT_SHELTER_CAPACITY,
    DEFAULT_WARNING_THRESHOLD_PCT,
    MAX_THRESHOLD_PCT,
    MIN_THRESHOLD_PCT,
    get_capacity_alerts,
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
# Metrics endpoint (RAP-250)
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
            description=("Days of history to include. Defaults: daily=30, weekly=90, monthly=365."),
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


# ---------------------------------------------------------------------------
# Capacity alerts endpoint (RAP-253)
# ---------------------------------------------------------------------------


class CapacityAlertSchema(BaseModel):
    severity: str
    title: str
    message: str
    occupancy_rate_pct: float
    recommended_action: str


class CapacityAlertsResponse(BaseModel):
    current_count: int
    capacity: int
    occupancy_rate_pct: float
    warning_threshold_pct: float
    critical_threshold_pct: float
    status: str
    alert_count: int
    alerts: list[CapacityAlertSchema]
    generated_at: str


@router.get(
    "/alerts",
    response_model=CapacityAlertsResponse,
    summary="Capacity alerts and threshold evaluation",
)
async def get_alerts(
    capacity: Annotated[
        int,
        Query(
            ge=MIN_CAPACITY,
            le=MAX_CAPACITY,
            description="Shelter capacity override (default: 200)",
        ),
    ] = DEFAULT_SHELTER_CAPACITY,
    warning_pct: Annotated[
        float,
        Query(
            ge=MIN_THRESHOLD_PCT,
            le=MAX_THRESHOLD_PCT,
            description=f"Warning threshold percentage (default: {DEFAULT_WARNING_THRESHOLD_PCT})",
        ),
    ] = DEFAULT_WARNING_THRESHOLD_PCT,
    critical_pct: Annotated[
        float,
        Query(
            ge=MIN_THRESHOLD_PCT,
            le=MAX_THRESHOLD_PCT,
            description=(
                f"Critical threshold percentage (default: {DEFAULT_CRITICAL_THRESHOLD_PCT})"
            ),
        ),
    ] = DEFAULT_CRITICAL_THRESHOLD_PCT,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> CapacityAlertsResponse:
    """Evaluate current shelter occupancy against configurable alert thresholds.

    Returns a list of active capacity alerts with severity, message, and
    recommended action. The **status** field gives a single summary level:
    - **ok**: occupancy is below the warning threshold
    - **warning**: occupancy is at or above `warning_pct`
    - **critical**: occupancy is at or above `critical_pct`

    Auth: requires staff or admin role.
    """
    result = await get_capacity_alerts(
        db,
        capacity=capacity,
        warning_threshold_pct=warning_pct,
        critical_threshold_pct=critical_pct,
    )

    return CapacityAlertsResponse(
        current_count=result.current_count,
        capacity=result.capacity,
        occupancy_rate_pct=result.occupancy_rate_pct,
        warning_threshold_pct=result.warning_threshold_pct,
        critical_threshold_pct=result.critical_threshold_pct,
        status=result.status,
        alert_count=len(result.alerts),
        alerts=[
            CapacityAlertSchema(
                severity=a.severity,
                title=a.title,
                message=a.message,
                occupancy_rate_pct=a.occupancy_rate_pct,
                recommended_action=a.recommended_action,
            )
            for a in result.alerts
        ],
        generated_at=result.generated_at,
    )


# ---------------------------------------------------------------------------
# Export endpoints (RAP-254)
# ---------------------------------------------------------------------------

# CSV headers for the full metrics export.
_METRICS_CSV_HEADERS = [
    "generated_at",
    "period_days",
    "capacity",
    "current_count",
    "occupancy_rate_pct",
    "intake_count",
    "outcome_count",
    "avg_los_days",
    "population_intake",
    "population_quarantine",
    "population_available",
    "population_foster",
    "population_under_treatment",
    "population_adopted",
    "population_deceased",
    "population_total",
    "species_dog",
    "species_cat",
    "species_other",
]

# CSV headers for the population breakdown export.
_POPULATION_CSV_HEADERS = [
    "generated_at",
    "status",
    "count",
    "occupancy_contribution",
]


@router.get(
    "/export/metrics",
    summary="CSV export of full operational metrics snapshot",
)
async def export_metrics_csv(
    period_days: Annotated[
        int,
        Query(
            ge=MIN_PERIOD_DAYS,
            le=MAX_PERIOD_DAYS,
            description="Lookback window in days (default: 30)",
        ),
    ] = DEFAULT_PERIOD_DAYS,
    capacity: Annotated[
        int,
        Query(
            ge=MIN_CAPACITY,
            le=MAX_CAPACITY,
            description="Shelter capacity override (default: 200)",
        ),
    ] = DEFAULT_SHELTER_CAPACITY,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export a CSV snapshot of the current operational metrics.

    The CSV contains one data row with all metric fields, suitable for
    importing into spreadsheets or external reporting tools.

    Auth: requires staff or admin role.
    """
    metrics = await get_operational_metrics(db, period_days=period_days, capacity=capacity)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(_METRICS_CSV_HEADERS)
    writer.writerow(
        [
            metrics.generated_at,
            metrics.period.period_days,
            metrics.occupancy.capacity,
            metrics.occupancy.current_count,
            metrics.occupancy.occupancy_rate_pct,
            metrics.period.intake_count,
            metrics.period.outcome_count,
            metrics.avg_los_days,
            metrics.population.intake,
            metrics.population.quarantine,
            metrics.population.available,
            metrics.population.foster,
            metrics.population.under_treatment,
            metrics.population.adopted,
            metrics.population.deceased,
            metrics.population.total,
            metrics.species.dog,
            metrics.species.cat,
            metrics.species.other,
        ]
    )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dashboard-metrics.csv"},
    )


@router.get(
    "/export/population",
    summary="CSV export of animal population breakdown",
)
async def export_population_csv(
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export a CSV breakdown of current animal population by status.

    Each row represents one status category with its animal count and
    contribution to shelter occupancy (sheltered = True for statuses that
    occupy a physical space).

    Auth: requires staff or admin role.
    """
    metrics = await get_operational_metrics(db)
    pop = metrics.population
    generated_at = metrics.generated_at

    # Statuses that contribute to physical occupancy of shelter space.
    occupancy_statuses = {"intake", "quarantine", "available", "under_treatment"}

    rows = [
        ("intake", pop.intake, "intake" in occupancy_statuses),
        ("quarantine", pop.quarantine, "quarantine" in occupancy_statuses),
        ("available", pop.available, "available" in occupancy_statuses),
        ("foster", pop.foster, "foster" in occupancy_statuses),
        ("under_treatment", pop.under_treatment, "under_treatment" in occupancy_statuses),
        ("adopted", pop.adopted, False),
        ("deceased", pop.deceased, False),
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(_POPULATION_CSV_HEADERS)
    for status, count, occupancy_contribution in rows:
        writer.writerow([generated_at, status, count, occupancy_contribution])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dashboard-population.csv"},
    )
