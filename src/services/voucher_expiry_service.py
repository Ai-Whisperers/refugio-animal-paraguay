"""Service for voucher expiry processing and refund policy.

Handles batch expiry of overdue vouchers and determines refund
eligibility based on configurable policy rules.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.vet_voucher import VetVoucher, VoucherStatus

logger = logging.getLogger(__name__)

# Refund policy: percentage refunded based on days remaining until expiry
# at the time of cancellation. Configured as (min_days, refund_pct).
REFUND_POLICY_TIERS: list[tuple[int, int]] = [
    (30, 100),  # 30+ days remaining: full refund
    (14, 75),  # 14-29 days: 75% refund
    (7, 50),  # 7-13 days: 50% refund
    (1, 25),  # 1-6 days: 25% refund
    (0, 0),  # Expired or same day: no refund
]

# Grace period after expiry during which a refund request can still be made
GRACE_PERIOD_DAYS = 7


class VoucherExpiryResult:
    """Result of a batch expiry run."""

    def __init__(self, expired_count: int, voucher_ids: list[UUID]) -> None:
        self.expired_count = expired_count
        self.voucher_ids = voucher_ids


class RefundEligibility:
    """Refund eligibility assessment for a voucher."""

    def __init__(
        self,
        eligible: bool,
        refund_percentage: int,
        refund_amount_pyg: int,
        reason: str,
    ) -> None:
        self.eligible = eligible
        self.refund_percentage = refund_percentage
        self.refund_amount_pyg = refund_amount_pyg
        self.reason = reason


def calculate_refund_percentage(expires_at: datetime, now: datetime | None = None) -> int:
    """Calculate refund percentage based on days remaining until expiry.

    Uses the REFUND_POLICY_TIERS configuration.
    """
    if now is None:
        now = datetime.now(UTC)

    days_remaining = (expires_at - now).days

    for min_days, percentage in REFUND_POLICY_TIERS:
        if days_remaining >= min_days:
            return percentage

    return 0


def assess_refund_eligibility(voucher: VetVoucher) -> RefundEligibility:
    """Assess whether a voucher is eligible for a refund and how much.

    Rules:
    - Only purchased or assigned vouchers can be refunded
    - Redeemed vouchers cannot be refunded
    - Expired vouchers can be refunded within the grace period
    - Cancelled vouchers that haven't been refunded yet can be assessed
    """
    now = datetime.now(UTC)

    # Already redeemed — no refund
    if voucher.status == VoucherStatus.REDEEMED:
        return RefundEligibility(
            eligible=False,
            refund_percentage=0,
            refund_amount_pyg=0,
            reason="Redeemed vouchers are not eligible for refund.",
        )

    # Expired — check grace period
    if voucher.status == VoucherStatus.EXPIRED:
        days_since_expiry = (now - voucher.expires_at).days
        if days_since_expiry <= GRACE_PERIOD_DAYS:
            return RefundEligibility(
                eligible=True,
                refund_percentage=25,
                refund_amount_pyg=int(voucher.amount_pyg * 0.25),
                reason=f"Expired within grace period ({days_since_expiry} days ago). 25% refund.",
            )
        return RefundEligibility(
            eligible=False,
            refund_percentage=0,
            refund_amount_pyg=0,
            reason=f"Expired {days_since_expiry} days ago. Grace period is {GRACE_PERIOD_DAYS} days.",
        )

    # Already cancelled — check if refund still possible
    if voucher.status == VoucherStatus.CANCELLED:
        return RefundEligibility(
            eligible=False,
            refund_percentage=0,
            refund_amount_pyg=0,
            reason="Voucher already cancelled. Refund should have been processed at cancellation.",
        )

    # Active voucher (purchased or assigned) — calculate based on time remaining
    refund_pct = calculate_refund_percentage(voucher.expires_at, now)
    refund_amount = int(voucher.amount_pyg * refund_pct / 100)

    return RefundEligibility(
        eligible=refund_pct > 0,
        refund_percentage=refund_pct,
        refund_amount_pyg=refund_amount,
        reason=f"{refund_pct}% refund based on time remaining until expiry.",
    )


async def expire_overdue_vouchers(db: AsyncSession) -> VoucherExpiryResult:
    """Find and expire all vouchers past their expiry date.

    Only processes vouchers in 'purchased' or 'assigned' status.
    Returns the count and IDs of expired vouchers.
    """
    now = datetime.now(UTC)

    # Find vouchers that should be expired
    query = select(VetVoucher.id).where(
        VetVoucher.status.in_([VoucherStatus.PURCHASED, VoucherStatus.ASSIGNED]),
        VetVoucher.expires_at < now,
    )

    result = await db.execute(query)
    voucher_ids = [row[0] for row in result.all()]

    if not voucher_ids:
        logger.info("No overdue vouchers found")
        return VoucherExpiryResult(expired_count=0, voucher_ids=[])

    # Batch update status
    stmt = (
        update(VetVoucher)
        .where(VetVoucher.id.in_(voucher_ids))
        .values(status=VoucherStatus.EXPIRED, updated_at=now)
    )
    await db.execute(stmt)
    await db.flush()

    logger.info("Expired %d overdue vouchers", len(voucher_ids))
    return VoucherExpiryResult(expired_count=len(voucher_ids), voucher_ids=voucher_ids)


async def get_expiring_soon_vouchers(db: AsyncSession, days_ahead: int = 7) -> list[VetVoucher]:
    """Get vouchers expiring within the specified number of days.

    Useful for sending expiry warning notifications.
    """
    now = datetime.now(UTC)
    cutoff = now + timedelta(days=days_ahead)

    result = await db.execute(
        select(VetVoucher)
        .where(
            VetVoucher.status.in_([VoucherStatus.PURCHASED, VoucherStatus.ASSIGNED]),
            VetVoucher.expires_at >= now,
            VetVoucher.expires_at <= cutoff,
        )
        .order_by(VetVoucher.expires_at)
    )

    return list(result.scalars().all())
