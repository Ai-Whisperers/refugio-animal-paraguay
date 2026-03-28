"""Public voucher statistics endpoints — unauthenticated, cached.

Endpoints:
  GET /api/public/vouchers/statistics  — aggregate voucher program stats
  GET /api/public/vouchers/recent      — recently redeemed vouchers
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.services.public_voucher_stats_service import (
    get_recent_redemptions,
    get_service_breakdown,
    get_top_clinics,
    get_voucher_statistics,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/public/vouchers",
    tags=["public-voucher-stats"],
)


# -- Response Schemas --


class ServiceBreakdownItem(BaseModel):
    """Service category with count."""

    category: str
    count: int


class TopClinicItem(BaseModel):
    """Top clinic by redemptions."""

    clinic_name: str
    city: str | None
    voucher_count: int


class RecentRedemptionItem(BaseModel):
    """Recently redeemed voucher for public display."""

    voucher_code: str
    service_category: str | None
    clinic_name: str | None
    redeemed_at: datetime | None
    amount_pyg: int


class VoucherStatisticsResponse(BaseModel):
    """Full public voucher statistics response."""

    total_vouchers_purchased: int = Field(..., description="Total non-cancelled vouchers")
    total_vouchers_redeemed: int = Field(..., description="Total redeemed vouchers")
    total_animals_treated: int = Field(..., description="Unique beneficiaries treated")
    active_clinics: int = Field(..., description="Number of active partner clinics")
    total_donated_eur: float = Field(..., description="Total EUR donated via vouchers")
    total_donated_pyg: int = Field(..., description="Total PYG donated via vouchers")
    service_breakdown: list[ServiceBreakdownItem] = Field(
        ..., description="Voucher usage by service category"
    )
    top_clinics: list[TopClinicItem] = Field(..., description="Top 5 clinics by redemption count")
    last_updated: datetime


class RecentRedemptionsResponse(BaseModel):
    """List of recently redeemed vouchers."""

    items: list[RecentRedemptionItem]
    count: int


# -- Endpoints --


@router.get(
    "/statistics",
    response_model=VoucherStatisticsResponse,
    summary="Public voucher program statistics",
    description="Aggregate statistics about the voucher program. Cached for 1 hour.",
)
async def voucher_statistics(
    db: AsyncSession = Depends(get_db),
) -> VoucherStatisticsResponse:
    """Return aggregate voucher program statistics."""
    stats = await get_voucher_statistics(db)
    breakdown = await get_service_breakdown(db)
    clinics = await get_top_clinics(db)

    return VoucherStatisticsResponse(
        total_vouchers_purchased=stats.total_vouchers_purchased,
        total_vouchers_redeemed=stats.total_vouchers_redeemed,
        total_animals_treated=stats.total_animals_treated,
        active_clinics=stats.active_clinics,
        total_donated_eur=stats.total_donated_eur,
        total_donated_pyg=stats.total_donated_pyg,
        service_breakdown=[
            ServiceBreakdownItem(category=b.category, count=b.count) for b in breakdown
        ],
        top_clinics=[
            TopClinicItem(clinic_name=c.clinic_name, city=c.city, voucher_count=c.voucher_count)
            for c in clinics
        ],
        last_updated=stats.last_updated,
    )


@router.get(
    "/recent",
    response_model=RecentRedemptionsResponse,
    summary="Recently redeemed vouchers",
    description="Last 10 redeemed vouchers for the public impact gallery. Cached for 1 hour.",
)
async def recent_redemptions(
    db: AsyncSession = Depends(get_db),
) -> RecentRedemptionsResponse:
    """Return most recently redeemed vouchers."""
    items = await get_recent_redemptions(db)
    return RecentRedemptionsResponse(
        items=[
            RecentRedemptionItem(
                voucher_code=r.voucher_code,
                service_category=r.service_category,
                clinic_name=r.clinic_name,
                redeemed_at=r.redeemed_at,
                amount_pyg=r.amount_pyg,
            )
            for r in items
        ],
        count=len(items),
    )
