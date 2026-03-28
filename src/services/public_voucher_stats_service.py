"""Public voucher statistics service — cached, unauthenticated metrics.

Provides aggregate statistics about the voucher program for the public
impact page. Caches results in-memory with configurable TTL.
"""

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.vet_clinic import ClinicStatus, VetClinic
from src.db.models.vet_voucher import VetVoucher, VoucherStatus

logger = logging.getLogger(__name__)

# Cache TTL: 1 hour (3600 seconds)
CACHE_TTL_SECONDS = 3600

# Module-level cache
_stats_cache: dict[str, tuple[float, "VoucherStatsResult"]] = {}
_recent_cache: dict[str, tuple[float, list["RecentRedemption"]]] = {}
_clinics_cache: dict[str, tuple[float, list["TopClinic"]]] = {}


@dataclass(frozen=True)
class VoucherStatsResult:
    """Aggregate voucher program statistics."""

    total_vouchers_purchased: int
    total_vouchers_redeemed: int
    total_animals_treated: int
    active_clinics: int
    total_donated_eur: float
    total_donated_pyg: int
    last_updated: datetime


@dataclass(frozen=True)
class ServiceBreakdown:
    """Breakdown of voucher usage by service category."""

    category: str
    count: int


@dataclass(frozen=True)
class RecentRedemption:
    """A recently redeemed voucher for public display."""

    voucher_code: str
    service_category: str | None
    clinic_name: str | None
    redeemed_at: datetime | None
    amount_pyg: int


@dataclass(frozen=True)
class TopClinic:
    """Top clinic by voucher redemptions."""

    clinic_name: str
    city: str | None
    voucher_count: int


def _get_cached(cache: dict, key: str, ttl: int = CACHE_TTL_SECONDS):
    """Return cached value if still valid, else None."""
    if key in cache:
        cached_at, value = cache[key]
        if time.monotonic() - cached_at < ttl:
            return value
    return None


async def get_voucher_statistics(db: AsyncSession) -> VoucherStatsResult:
    """Return aggregate voucher program statistics with caching."""
    cached = _get_cached(_stats_cache, "stats")
    if cached is not None:
        return cached

    # Total purchased (all statuses except cancelled)
    total_purchased_q = sa.select(sa.func.count()).where(
        VetVoucher.status != VoucherStatus.CANCELLED
    )
    total_purchased = (await db.execute(total_purchased_q)).scalar_one()

    # Total redeemed
    total_redeemed_q = sa.select(sa.func.count()).where(VetVoucher.status == VoucherStatus.REDEEMED)
    total_redeemed = (await db.execute(total_redeemed_q)).scalar_one()

    # Unique animals treated (approximate: count distinct beneficiary_id on redeemed)
    animals_treated_q = sa.select(sa.func.count(sa.distinct(VetVoucher.beneficiary_id))).where(
        VetVoucher.status == VoucherStatus.REDEEMED,
        VetVoucher.beneficiary_id.isnot(None),
    )
    animals_treated = (await db.execute(animals_treated_q)).scalar_one()

    # Active clinics
    active_clinics_q = sa.select(sa.func.count()).where(VetClinic.status == ClinicStatus.ACTIVE)
    active_clinics = (await db.execute(active_clinics_q)).scalar_one()

    # Total donated (redeemed vouchers)
    donated_q = sa.select(
        sa.func.coalesce(sa.func.sum(VetVoucher.amount_eur), 0.0).label("eur"),
        sa.func.coalesce(sa.func.sum(VetVoucher.amount_pyg), 0).label("pyg"),
    ).where(VetVoucher.status == VoucherStatus.REDEEMED)
    donated = (await db.execute(donated_q)).one()

    result = VoucherStatsResult(
        total_vouchers_purchased=total_purchased,
        total_vouchers_redeemed=total_redeemed,
        total_animals_treated=animals_treated,
        active_clinics=active_clinics,
        total_donated_eur=round(float(donated.eur), 2),
        total_donated_pyg=int(donated.pyg),
        last_updated=datetime.now(UTC),
    )

    _stats_cache["stats"] = (time.monotonic(), result)
    return result


async def get_service_breakdown(db: AsyncSession) -> list[ServiceBreakdown]:
    """Return breakdown of redeemed vouchers by service category."""
    q = (
        sa.select(
            sa.func.coalesce(VetVoucher.service_category, "Other").label("category"),
            sa.func.count().label("cnt"),
        )
        .where(VetVoucher.status == VoucherStatus.REDEEMED)
        .group_by(sa.func.coalesce(VetVoucher.service_category, "Other"))
        .order_by(sa.desc("cnt"))
    )
    result = await db.execute(q)
    return [ServiceBreakdown(category=row.category, count=row.cnt) for row in result.all()]


async def get_recent_redemptions(db: AsyncSession, *, limit: int = 10) -> list[RecentRedemption]:
    """Return most recently redeemed vouchers for public display."""
    cached = _get_cached(_recent_cache, "recent")
    if cached is not None:
        return cached

    q = (
        sa.select(
            VetVoucher.code,
            VetVoucher.service_category,
            VetVoucher.redeemed_at,
            VetVoucher.amount_pyg,
            VetClinic.name.label("clinic_name"),
        )
        .outerjoin(VetClinic, VetVoucher.redeemed_clinic_id == VetClinic.id)
        .where(VetVoucher.status == VoucherStatus.REDEEMED)
        .where(VetVoucher.redeemed_at.isnot(None))
        .order_by(VetVoucher.redeemed_at.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    items = [
        RecentRedemption(
            voucher_code=row.code,
            service_category=row.service_category,
            clinic_name=row.clinic_name,
            redeemed_at=row.redeemed_at,
            amount_pyg=row.amount_pyg,
        )
        for row in result.all()
    ]

    _recent_cache["recent"] = (time.monotonic(), items)
    return items


async def get_top_clinics(db: AsyncSession, *, limit: int = 5) -> list[TopClinic]:
    """Return top clinics by number of redeemed vouchers."""
    cached = _get_cached(_clinics_cache, "top_clinics")
    if cached is not None:
        return cached

    q = (
        sa.select(
            VetClinic.name.label("clinic_name"),
            VetClinic.city.label("city"),
            sa.func.count().label("voucher_count"),
        )
        .join(VetClinic, VetVoucher.redeemed_clinic_id == VetClinic.id)
        .where(VetVoucher.status == VoucherStatus.REDEEMED)
        .group_by(VetClinic.id, VetClinic.name, VetClinic.city)
        .order_by(sa.desc("voucher_count"))
        .limit(limit)
    )
    result = await db.execute(q)
    items = [
        TopClinic(
            clinic_name=row.clinic_name,
            city=row.city,
            voucher_count=row.voucher_count,
        )
        for row in result.all()
    ]

    _clinics_cache["top_clinics"] = (time.monotonic(), items)
    return items


def clear_cache() -> None:
    """Clear all in-memory caches. Useful for testing."""
    _stats_cache.clear()
    _recent_cache.clear()
    _clinics_cache.clear()
