"""Monthly impact aggregation service for the public /impact page.

Computes per-month counts of animals rescued, adoptions completed,
castrations performed, and donation totals for the last 12 months.
Results are cached in memory for 1 hour.
"""

import time
from dataclasses import dataclass
from datetime import UTC, date, datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.db.models.animal import Animal
from src.db.models.donation import Donation, DonationStatus
from src.db.models.surgery import Surgery

# Cache TTL in seconds (1 hour)
IMPACT_CACHE_TTL_SECONDS = 3600

# Number of trailing months to return
TRAILING_MONTHS = 12

# Surgery type counted as castration
CASTRATION_SURGERY_TYPE = "castration"


@dataclass(frozen=True)
class MonthlyImpact:
    """Aggregated metrics for a single calendar month."""

    year: int
    month: int
    animals_rescued: int
    adoptions_completed: int
    castrations_performed: int
    donations_total_cents: int


@dataclass(frozen=True)
class ImpactSummary:
    """Complete impact response: all-time totals + monthly breakdown."""

    total_animals_rescued: int
    total_adopted: int
    total_castrated: int
    total_donations_cents: int
    months: list[MonthlyImpact]
    last_updated: datetime


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class _ImpactCache:
    """In-memory cache for the monthly impact data."""

    def __init__(self, ttl: int = IMPACT_CACHE_TTL_SECONDS) -> None:
        self._ttl = ttl
        self._value: ImpactSummary | None = None
        self._at: float = 0.0

    @property
    def cached(self) -> ImpactSummary | None:
        if self._value is not None and (time.monotonic() - self._at) < self._ttl:
            return self._value
        return None

    def set(self, v: ImpactSummary) -> None:
        self._value = v
        self._at = time.monotonic()

    def invalidate(self) -> None:
        self._value = None


_cache = _ImpactCache()


def get_impact_cache() -> _ImpactCache:
    """Expose for test injection."""
    return _cache


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


def _month_range(year: int, month: int) -> tuple[datetime, datetime]:
    """Return (start, end) datetimes for a calendar month (UTC)."""
    start = datetime(year, month, 1, tzinfo=UTC)
    end_date = date(year, month, 1) + relativedelta(months=1)
    end = datetime(end_date.year, end_date.month, end_date.day, tzinfo=UTC)
    return start, end


async def _monthly_animals(db: AsyncSession, start: datetime, end: datetime) -> int:
    result = await db.execute(
        select(func.count(Animal.id)).where(
            Animal.created_at >= start,
            Animal.created_at < end,
        )
    )
    return result.scalar_one()


async def _monthly_adoptions(db: AsyncSession, start: datetime, end: datetime) -> int:
    result = await db.execute(
        select(func.count(AdoptionRequest.id)).where(
            AdoptionRequest.status == AdoptionRequestStatus.APPROVED,
            AdoptionRequest.updated_at >= start,
            AdoptionRequest.updated_at < end,
        )
    )
    return result.scalar_one()


async def _monthly_castrations(db: AsyncSession, start: datetime, end: datetime) -> int:
    result = await db.execute(
        select(func.count(Surgery.id)).where(
            Surgery.surgery_type == CASTRATION_SURGERY_TYPE,
            Surgery.surgery_status == "completed",
            Surgery.created_at >= start,
            Surgery.created_at < end,
        )
    )
    return result.scalar_one()


async def _monthly_donations(db: AsyncSession, start: datetime, end: datetime) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(Donation.amount_cents), 0)).where(
            Donation.status == DonationStatus.COMPLETED,
            Donation.created_at >= start,
            Donation.created_at < end,
        )
    )
    return result.scalar_one()


# ---------------------------------------------------------------------------
# All-time totals (reused from public_statistics_service logic)
# ---------------------------------------------------------------------------


async def _total_animals(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(Animal.id)))
    return result.scalar_one()


async def _total_adopted(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count(AdoptionRequest.id)).where(
            AdoptionRequest.status == AdoptionRequestStatus.APPROVED,
        )
    )
    return result.scalar_one()


async def _total_castrated(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count(Surgery.id)).where(
            Surgery.surgery_type == CASTRATION_SURGERY_TYPE,
            Surgery.surgery_status == "completed",
        )
    )
    return result.scalar_one()


async def _total_donations(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(Donation.amount_cents), 0)).where(
            Donation.status == DonationStatus.COMPLETED,
        )
    )
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_impact_summary(db: AsyncSession) -> ImpactSummary:
    """Compute monthly impact data for the last 12 months + all-time totals."""
    today = date.today()
    months: list[MonthlyImpact] = []

    for i in range(TRAILING_MONTHS - 1, -1, -1):
        target = today - relativedelta(months=i)
        start, end = _month_range(target.year, target.month)
        animals = await _monthly_animals(db, start, end)
        adoptions = await _monthly_adoptions(db, start, end)
        castrations = await _monthly_castrations(db, start, end)
        donations = await _monthly_donations(db, start, end)
        months.append(
            MonthlyImpact(
                year=target.year,
                month=target.month,
                animals_rescued=animals,
                adoptions_completed=adoptions,
                castrations_performed=castrations,
                donations_total_cents=donations,
            )
        )

    total_a = await _total_animals(db)
    total_ad = await _total_adopted(db)
    total_c = await _total_castrated(db)
    total_d = await _total_donations(db)

    return ImpactSummary(
        total_animals_rescued=total_a,
        total_adopted=total_ad,
        total_castrated=total_c,
        total_donations_cents=total_d,
        months=months,
        last_updated=datetime.now(UTC),
    )


async def get_impact_summary(
    db: AsyncSession,
    cache: _ImpactCache | None = None,
) -> ImpactSummary:
    """Return cached impact summary, refreshing when expired."""
    c = cache if cache is not None else _cache
    cached = c.cached
    if cached is not None:
        return cached
    summary = await fetch_impact_summary(db)
    c.set(summary)
    return summary
