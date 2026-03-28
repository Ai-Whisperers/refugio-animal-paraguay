"""Public statistics service — aggregates shelter metrics with in-memory caching.

Provides a single public-facing endpoint's data: total animals rescued,
total adopted, total castrated, total donors, total donation amount, and
total volunteers. Cached for 5 minutes to keep response times under 100ms.
"""

import time
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.animal import Animal, AnimalStatus
from src.db.models.donation import Donation, DonationStatus
from src.db.models.surgery import Surgery
from src.db.models.user_role import UserRoleAssignment

# Cache TTL in seconds (5 minutes)
CACHE_TTL_SECONDS = 300

# Surgery type value that counts as castration
CASTRATION_SURGERY_TYPE = "castration"

# Volunteer role name
VOLUNTEER_ROLE = "volunteer"


@dataclass(frozen=True)
class PublicStatistics:
    """Immutable snapshot of aggregated shelter statistics."""

    total_animals_rescued: int
    total_adopted: int
    total_castrated: int
    total_donors: int
    total_donations_amount_cents: int
    total_volunteers: int
    last_updated: datetime


class PublicStatisticsCache:
    """Simple in-memory cache for public statistics.

    Thread-safe for async usage since Python's GIL prevents concurrent
    writes to the instance attributes.
    """

    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
        self._ttl_seconds = ttl_seconds
        self._cached: PublicStatistics | None = None
        self._cached_at: float = 0.0

    @property
    def is_valid(self) -> bool:
        """Check whether the cached value is still within TTL."""
        if self._cached is None:
            return False
        return (time.monotonic() - self._cached_at) < self._ttl_seconds

    @property
    def cached_value(self) -> PublicStatistics | None:
        """Return cached statistics if still valid, else None."""
        if self.is_valid:
            return self._cached
        return None

    def set(self, stats: PublicStatistics) -> None:
        """Store a new statistics snapshot."""
        self._cached = stats
        self._cached_at = time.monotonic()

    def invalidate(self) -> None:
        """Force cache expiry on next read."""
        self._cached = None
        self._cached_at = 0.0


# Module-level singleton cache
_cache = PublicStatisticsCache()


def get_cache() -> PublicStatisticsCache:
    """Return the module-level statistics cache (for DI / testing)."""
    return _cache


async def _count_animals_rescued(db: AsyncSession) -> int:
    """Count all animals ever entered into the system."""
    result = await db.execute(select(func.count(Animal.id)))
    return result.scalar_one()


async def _count_adopted(db: AsyncSession) -> int:
    """Count animals with status 'adopted'."""
    result = await db.execute(
        select(func.count(Animal.id)).where(
            Animal.status == AnimalStatus.ADOPTED.value,
        )
    )
    return result.scalar_one()


async def _count_castrated(db: AsyncSession) -> int:
    """Count surgeries of type 'castration' that have been completed."""
    result = await db.execute(
        select(func.count(Surgery.id)).where(
            Surgery.surgery_type == CASTRATION_SURGERY_TYPE,
            Surgery.surgery_status == "completed",
        )
    )
    return result.scalar_one()


async def _count_donors(db: AsyncSession) -> int:
    """Count unique donors who have at least one completed donation."""
    result = await db.execute(
        select(func.count(func.distinct(Donation.donor_id))).where(
            Donation.donor_id.isnot(None),
            Donation.status == DonationStatus.COMPLETED.value,
        )
    )
    return result.scalar_one()


async def _sum_donations(db: AsyncSession) -> int:
    """Sum of all completed donation amounts in cents."""
    result = await db.execute(
        select(func.coalesce(func.sum(Donation.amount_cents), 0)).where(
            Donation.status == DonationStatus.COMPLETED.value,
        )
    )
    return result.scalar_one()


async def _count_volunteers(db: AsyncSession) -> int:
    """Count users assigned the volunteer role."""
    result = await db.execute(
        select(func.count(func.distinct(UserRoleAssignment.user_id))).where(
            UserRoleAssignment.role == VOLUNTEER_ROLE,
        )
    )
    return result.scalar_one()


async def fetch_public_statistics(db: AsyncSession) -> PublicStatistics:
    """Compute fresh statistics from the database."""
    total_animals = await _count_animals_rescued(db)
    total_adopted = await _count_adopted(db)
    total_castrated = await _count_castrated(db)
    total_donors = await _count_donors(db)
    total_amount = await _sum_donations(db)
    total_volunteers = await _count_volunteers(db)

    return PublicStatistics(
        total_animals_rescued=total_animals,
        total_adopted=total_adopted,
        total_castrated=total_castrated,
        total_donors=total_donors,
        total_donations_amount_cents=total_amount,
        total_volunteers=total_volunteers,
        last_updated=datetime.now(UTC),
    )


async def get_public_statistics(
    db: AsyncSession,
    cache: PublicStatisticsCache | None = None,
) -> PublicStatistics:
    """Return cached statistics, refreshing from DB when cache has expired.

    Parameters
    ----------
    db : AsyncSession
        Database session for querying aggregate counts.
    cache : PublicStatisticsCache | None
        Optional cache override (used in tests). Defaults to module singleton.
    """
    if cache is None:
        cache = _cache

    cached = cache.cached_value
    if cached is not None:
        return cached

    stats = await fetch_public_statistics(db)
    cache.set(stats)
    return stats
