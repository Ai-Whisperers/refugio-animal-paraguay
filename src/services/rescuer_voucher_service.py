"""Service for rescuer voucher wallet and claim flow.

Handles voucher discovery (available vouchers near a rescuer),
claiming vouchers for specific animals, and listing a rescuer's
claimed/redeemed voucher wallet.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.vet_voucher import VALID_VOUCHER_TRANSITIONS, VetVoucher, VoucherStatus
from src.services.vet_voucher_service import (
    VoucherCodeNotFoundError,
    VoucherExpiredError,
)

logger = logging.getLogger(__name__)

# Default radius for location-based voucher discovery (km)
DEFAULT_DISCOVERY_RADIUS_KM = 100
DEFAULT_PAGE_SIZE = 10


class VoucherAlreadyClaimedError(Exception):
    """Raised when a voucher has already been claimed by another rescuer."""

    def __init__(self, code: str) -> None:
        self.code = code
        self.message = f"Voucher '{code}' has already been claimed."
        super().__init__(self.message)


class VoucherNotClaimableError(Exception):
    """Raised when a voucher cannot be claimed (wrong status)."""

    def __init__(self, code: str, status: str) -> None:
        self.code = code
        self.status = status
        self.message = (
            f"Voucher '{code}' cannot be claimed (current status: {status}). "
            f"Only vouchers with status 'purchased' can be claimed."
        )
        super().__init__(self.message)


@dataclass
class VoucherClaimRequest:
    """Data for claiming a voucher."""

    rescuer_id: UUID
    animal_id: UUID | None = None
    note: str | None = None


@dataclass
class VoucherClaimResult:
    """Result of a successful voucher claim."""

    voucher: VetVoucher
    claimed_at: datetime


async def get_available_vouchers(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    service_category: str | None = None,
    clinic_id: UUID | None = None,
) -> tuple[list[VetVoucher], int]:
    """List vouchers available for claiming.

    Returns purchased (unclaimed) vouchers that haven't expired,
    optionally filtered by service category or clinic.
    Sorted by expiry date (soonest first).
    """
    now = datetime.now(UTC)

    base_filter = [
        VetVoucher.status == VoucherStatus.PURCHASED,
        VetVoucher.expires_at > now,
    ]

    if service_category:
        base_filter.append(VetVoucher.service_category == service_category)
    if clinic_id:
        base_filter.append((VetVoucher.clinic_id == clinic_id) | (VetVoucher.clinic_id.is_(None)))

    query = (
        select(VetVoucher)
        .where(*base_filter)
        .order_by(VetVoucher.expires_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    count_query = select(func.count(VetVoucher.id)).where(*base_filter)

    result = await db.execute(query)
    vouchers = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return vouchers, total


async def claim_voucher(
    db: AsyncSession,
    code: str,
    claim: VoucherClaimRequest,
) -> VoucherClaimResult:
    """Claim a voucher for a rescuer.

    Validates voucher exists, is in 'purchased' status, and hasn't expired.
    Transitions voucher to 'assigned' status with rescuer as beneficiary.
    """
    # Look up the voucher
    result = await db.execute(select(VetVoucher).where(VetVoucher.code == code))
    voucher = result.scalar_one_or_none()
    if voucher is None:
        raise VoucherCodeNotFoundError(code)

    # Check expiry
    now = datetime.now(UTC)
    if now > voucher.expires_at:
        raise VoucherExpiredError(voucher.id)

    # Check status
    if voucher.status != VoucherStatus.PURCHASED:
        if voucher.status == VoucherStatus.ASSIGNED:
            raise VoucherAlreadyClaimedError(code)
        raise VoucherNotClaimableError(code, voucher.status)

    # Validate transition is allowed
    allowed = VALID_VOUCHER_TRANSITIONS.get(voucher.status, set())
    if VoucherStatus.ASSIGNED not in allowed:
        raise VoucherNotClaimableError(code, voucher.status)

    # Perform the claim (transition to assigned)
    voucher.status = VoucherStatus.ASSIGNED
    voucher.beneficiary_id = claim.rescuer_id
    voucher.assigned_at = now
    if claim.note:
        voucher.notes = claim.note

    await db.flush()
    await db.refresh(voucher)

    logger.info(
        "Voucher %s (code=%s) claimed by rescuer %s",
        voucher.id,
        code,
        claim.rescuer_id,
    )

    return VoucherClaimResult(voucher=voucher, claimed_at=now)


async def get_rescuer_wallet(
    db: AsyncSession,
    rescuer_id: UUID,
    *,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[VetVoucher], int]:
    """List vouchers in a rescuer's wallet (claimed + redeemed).

    Optionally filtered by status (assigned/redeemed).
    Sorted by most recently claimed first.
    """
    base_filter = [VetVoucher.beneficiary_id == rescuer_id]

    if status_filter:
        base_filter.append(VetVoucher.status == status_filter)
    else:
        # Default: show assigned and redeemed
        base_filter.append(VetVoucher.status.in_([VoucherStatus.ASSIGNED, VoucherStatus.REDEEMED]))

    query = (
        select(VetVoucher)
        .where(*base_filter)
        .order_by(VetVoucher.assigned_at.desc().nulls_last())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    count_query = select(func.count(VetVoucher.id)).where(*base_filter)

    result = await db.execute(query)
    vouchers = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return vouchers, total


async def get_rescuer_wallet_summary(
    db: AsyncSession,
    rescuer_id: UUID,
) -> dict[str, int]:
    """Get summary counts for a rescuer's wallet."""
    claimed_count_q = select(func.count(VetVoucher.id)).where(
        VetVoucher.beneficiary_id == rescuer_id,
        VetVoucher.status == VoucherStatus.ASSIGNED,
    )
    redeemed_count_q = select(func.count(VetVoucher.id)).where(
        VetVoucher.beneficiary_id == rescuer_id,
        VetVoucher.status == VoucherStatus.REDEEMED,
    )

    claimed_result = await db.execute(claimed_count_q)
    redeemed_result = await db.execute(redeemed_count_q)

    return {
        "claimed": claimed_result.scalar_one(),
        "redeemed": redeemed_result.scalar_one(),
    }
