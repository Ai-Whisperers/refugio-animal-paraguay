"""Operational metrics service for shelter dashboard (RAP-250, RAP-252).

Aggregates live data from the database to produce shelter operational KPIs:
- Population breakdown by status
- Occupancy metrics
- Intake and outcome counts for a configurable period
- Species breakdown
- Average length of stay for sheltered animals
- Time-series trend data (daily / weekly / monthly)

All queries are async and run against the live database.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import case, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Integer

from src.db.models.animal import Animal, AnimalStatus

logger = logging.getLogger(__name__)

# Shelter capacity — total spaces available.
# Can be overridden at call time; this is the operational default.
DEFAULT_SHELTER_CAPACITY = 200

# Statuses that represent animals currently in the shelter (occupying a space).
SHELTERED_STATUSES = {
    AnimalStatus.INTAKE,
    AnimalStatus.QUARANTINE,
    AnimalStatus.AVAILABLE,
    AnimalStatus.UNDER_TREATMENT,
}

# Statuses that represent positive outcomes (animals that left the shelter alive
# through a planned channel — e.g. adoption, foster placement).
POSITIVE_OUTCOME_STATUSES = {AnimalStatus.ADOPTED}

# ---------------------------------------------------------------------------
# Data classes returned by the service
# ---------------------------------------------------------------------------


class PopulationBreakdown:
    """Animal counts grouped by status."""

    __slots__ = (
        "adopted",
        "available",
        "deceased",
        "foster",
        "intake",
        "quarantine",
        "total",
        "under_treatment",
    )

    def __init__(
        self,
        intake: int,
        quarantine: int,
        available: int,
        foster: int,
        under_treatment: int,
        adopted: int,
        deceased: int,
    ) -> None:
        self.intake = intake
        self.quarantine = quarantine
        self.available = available
        self.foster = foster
        self.under_treatment = under_treatment
        self.adopted = adopted
        self.deceased = deceased
        self.total = intake + quarantine + available + foster + under_treatment


class OccupancyMetrics:
    """Current occupancy vs. shelter capacity."""

    __slots__ = ("capacity", "current_count", "occupancy_rate_pct")

    def __init__(self, current_count: int, capacity: int) -> None:
        self.current_count = current_count
        self.capacity = capacity
        self.occupancy_rate_pct = round(current_count / capacity * 100, 1) if capacity > 0 else 0.0


class PeriodCounts:
    """Intake and outcome counts for a given time window."""

    __slots__ = ("intake_count", "outcome_count", "period_days")

    def __init__(self, period_days: int, intake_count: int, outcome_count: int) -> None:
        self.period_days = period_days
        self.intake_count = intake_count
        self.outcome_count = outcome_count


class SpeciesBreakdown:
    """Current sheltered animal counts by species."""

    __slots__ = ("cat", "dog", "other")

    def __init__(self, dog: int, cat: int, other: int) -> None:
        self.dog = dog
        self.cat = cat
        self.other = other


class OperationalMetrics:
    """Aggregated operational metrics for the shelter dashboard."""

    __slots__ = (
        "avg_los_days",
        "generated_at",
        "occupancy",
        "period",
        "population",
        "species",
    )

    def __init__(
        self,
        generated_at: str,
        population: PopulationBreakdown,
        occupancy: OccupancyMetrics,
        period: PeriodCounts,
        species: SpeciesBreakdown,
        avg_los_days: float,
    ) -> None:
        self.generated_at = generated_at
        self.population = population
        self.occupancy = occupancy
        self.period = period
        self.species = species
        self.avg_los_days = avg_los_days


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


async def _get_population_breakdown(db: AsyncSession) -> PopulationBreakdown:
    """Query animal counts grouped by status."""
    stmt = select(
        func.sum(cast(case((Animal.status == AnimalStatus.INTAKE, 1), else_=0), Integer)).label(
            "intake"
        ),
        func.sum(cast(case((Animal.status == AnimalStatus.QUARANTINE, 1), else_=0), Integer)).label(
            "quarantine"
        ),
        func.sum(cast(case((Animal.status == AnimalStatus.AVAILABLE, 1), else_=0), Integer)).label(
            "available"
        ),
        func.sum(cast(case((Animal.status == AnimalStatus.FOSTER, 1), else_=0), Integer)).label(
            "foster"
        ),
        func.sum(
            cast(case((Animal.status == AnimalStatus.UNDER_TREATMENT, 1), else_=0), Integer)
        ).label("under_treatment"),
        func.sum(cast(case((Animal.status == AnimalStatus.ADOPTED, 1), else_=0), Integer)).label(
            "adopted"
        ),
        func.sum(cast(case((Animal.status == AnimalStatus.DECEASED, 1), else_=0), Integer)).label(
            "deceased"
        ),
    )
    result = await db.execute(stmt)
    row = result.one()
    return PopulationBreakdown(
        intake=row.intake or 0,
        quarantine=row.quarantine or 0,
        available=row.available or 0,
        foster=row.foster or 0,
        under_treatment=row.under_treatment or 0,
        adopted=row.adopted or 0,
        deceased=row.deceased or 0,
    )


async def _get_period_counts(db: AsyncSession, period_days: int) -> PeriodCounts:
    """Count intake and outcome events within the given lookback window.

    Intake = animals created (entered the system) in the period.
    Outcome = animals moved to an adopted status in the period.
    SQLAlchemy does not have a direct "updated_at" column for status changes,
    so we approximate: intake uses created_at; outcomes use created_at of adopted animals
    as a conservative lower bound. A future migration can add an outcome_at column.
    """
    since = datetime.now(UTC) - timedelta(days=period_days)

    intake_stmt = select(func.count(Animal.id)).where(
        Animal.created_at >= since,
    )
    intake_result = await db.execute(intake_stmt)
    intake_count = intake_result.scalar_one() or 0

    # Count animals currently adopted whose created_at falls within the window
    # (approximation until an outcome_at column is added).
    outcome_stmt = select(func.count(Animal.id)).where(
        Animal.status == AnimalStatus.ADOPTED,
        Animal.created_at >= since,
    )
    outcome_result = await db.execute(outcome_stmt)
    outcome_count = outcome_result.scalar_one() or 0

    return PeriodCounts(
        period_days=period_days,
        intake_count=intake_count,
        outcome_count=outcome_count,
    )


async def _get_species_breakdown(db: AsyncSession) -> SpeciesBreakdown:
    """Count sheltered animals (in-facility) by species."""
    sheltered_statuses = [s.value for s in SHELTERED_STATUSES]
    stmt = select(
        func.sum(
            cast(
                case((Animal.species == "dog", 1), else_=0),
                Integer,
            )
        ).label("dog"),
        func.sum(
            cast(
                case((Animal.species == "cat", 1), else_=0),
                Integer,
            )
        ).label("cat"),
        func.sum(
            cast(
                case(((Animal.species != "dog") & (Animal.species != "cat"), 1), else_=0),
                Integer,
            )
        ).label("other"),
    ).where(Animal.status.in_(sheltered_statuses))
    result = await db.execute(stmt)
    row = result.one()
    return SpeciesBreakdown(
        dog=row.dog or 0,
        cat=row.cat or 0,
        other=row.other or 0,
    )


async def _get_avg_los_days(db: AsyncSession) -> float:
    """Compute average length of stay (days) for currently sheltered animals.

    Uses created_at as the arrival proxy. Animals in foster care are excluded
    since they are not occupying a physical shelter space.
    """
    sheltered_statuses = [s.value for s in SHELTERED_STATUSES - {AnimalStatus.FOSTER}]
    stmt = select(
        func.coalesce(
            func.avg(func.extract("epoch", func.now() - Animal.created_at) / 86400),
            0.0,
        ).label("avg_los")
    ).where(Animal.status.in_(sheltered_statuses))
    result = await db.execute(stmt)
    avg_los = result.scalar_one() or 0.0
    return round(float(avg_los), 1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_operational_metrics(
    db: AsyncSession,
    period_days: int = 30,
    capacity: int = DEFAULT_SHELTER_CAPACITY,
) -> OperationalMetrics:
    """Aggregate all operational metrics from the live database.

    Args:
        db: Async SQLAlchemy session.
        period_days: Lookback window for intake/outcome counts.
        capacity: Shelter maximum capacity for occupancy calculations.

    Returns:
        OperationalMetrics dataclass with all aggregated values.
    """
    population = await _get_population_breakdown(db)
    occupancy = OccupancyMetrics(current_count=population.total, capacity=capacity)
    period = await _get_period_counts(db, period_days)
    species = await _get_species_breakdown(db)
    avg_los = await _get_avg_los_days(db)

    return OperationalMetrics(
        generated_at=datetime.now(UTC).isoformat(),
        population=population,
        occupancy=occupancy,
        period=period,
        species=species,
        avg_los_days=avg_los,
    )


# ---------------------------------------------------------------------------
# Trend data (RAP-252)
# ---------------------------------------------------------------------------

# Valid grouping intervals for trend queries.
TrendInterval = Literal["daily", "weekly", "monthly"]

# Maximum number of data points per interval to avoid overwhelming the caller.
MAX_TREND_POINTS = 90


class TrendDataPoint:
    """A single time-series data point for the trend chart."""

    __slots__ = ("intake_count", "outcome_count", "period_label")

    def __init__(self, period_label: str, intake_count: int, outcome_count: int) -> None:
        self.period_label = period_label
        self.intake_count = intake_count
        self.outcome_count = outcome_count


class TrendData:
    """Time-series trend data for the operational dashboard."""

    __slots__ = ("data_points", "generated_at", "interval", "lookback_days")

    def __init__(
        self,
        interval: str,
        lookback_days: int,
        data_points: list[TrendDataPoint],
        generated_at: str,
    ) -> None:
        self.interval = interval
        self.lookback_days = lookback_days
        self.data_points = data_points
        self.generated_at = generated_at


# Mapping from interval name to PostgreSQL date_trunc value and lookback window.
_INTERVAL_CONFIG: dict[str, dict[str, object]] = {
    "daily": {"trunc": "day", "default_days": 30},
    "weekly": {"trunc": "week", "default_days": 90},
    "monthly": {"trunc": "month", "default_days": 365},
}

# Format strings for display labels per interval.
_LABEL_FORMAT: dict[str, str] = {
    "daily": "%d/%m",
    "weekly": "Sem %W",
    "monthly": "%b %Y",
}


async def get_trend_data(
    db: AsyncSession,
    interval: TrendInterval = "monthly",
    lookback_days: int | None = None,
) -> TrendData:
    """Compute intake/outcome time-series data grouped by the given interval.

    Uses created_at as the intake proxy and approximates outcomes via adopted
    animals created within the window (consistent with get_operational_metrics).

    Args:
        db: Async SQLAlchemy session.
        interval: Grouping interval — "daily", "weekly", or "monthly".
        lookback_days: Days of history to include. Defaults per interval:
            daily=30, weekly=90, monthly=365.

    Returns:
        TrendData with a list of TrendDataPoint sorted ascending by date.
    """
    config = _INTERVAL_CONFIG[interval]
    trunc_value: str = str(config["trunc"])
    days: int = lookback_days if lookback_days is not None else int(str(config["default_days"]))
    since = datetime.now(UTC) - timedelta(days=days)

    # Build grouped intake counts.
    intake_stmt = (
        select(
            func.date_trunc(trunc_value, Animal.created_at).label("period"),
            func.count(Animal.id).label("intake_count"),
        )
        .where(Animal.created_at >= since)
        .group_by(text("period"))
        .order_by(text("period"))
    )

    # Build grouped outcome counts (adopted animals as proxy).
    outcome_stmt = (
        select(
            func.date_trunc(trunc_value, Animal.created_at).label("period"),
            func.count(Animal.id).label("outcome_count"),
        )
        .where(
            Animal.status == AnimalStatus.ADOPTED,
            Animal.created_at >= since,
        )
        .group_by(text("period"))
        .order_by(text("period"))
    )

    intake_result = await db.execute(intake_stmt)
    outcome_result = await db.execute(outcome_stmt)

    intake_rows = {row.period: row.intake_count for row in intake_result}
    outcome_rows = {row.period: row.outcome_count for row in outcome_result}

    # Merge the two sets of periods into unified data points.
    all_periods = sorted(set(intake_rows.keys()) | set(outcome_rows.keys()))

    label_fmt = _LABEL_FORMAT[interval]
    data_points = [
        TrendDataPoint(
            period_label=period.strftime(label_fmt) if hasattr(period, "strftime") else str(period),
            intake_count=intake_rows.get(period, 0),
            outcome_count=outcome_rows.get(period, 0),
        )
        for period in all_periods[-MAX_TREND_POINTS:]
    ]

    return TrendData(
        interval=interval,
        lookback_days=days,
        data_points=data_points,
        generated_at=datetime.now(UTC).isoformat(),
    )
