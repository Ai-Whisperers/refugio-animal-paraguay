"""Service layer for veterinary voucher lifecycle management.

Handles voucher creation, assignment, redemption, cancellation, and
expiry. Enforces status transition rules and validates relationships.
"""

import logging
import secrets
import string
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.vet_voucher import VALID_VOUCHER_TRANSITIONS, VetVoucher, VoucherStatus

logger = logging.getLogger(__name__)

# Voucher code alphabet (uppercase + digits, no ambiguous chars)
_CODE_ALPHABET = string.ascii_uppercase.replace("O", "").replace("I", "") + string.digits.replace(
    "0", ""
).replace("1", "")
VOUCHER_CODE_LENGTH = 8


class VoucherNotFoundError(Exception):
    """Raised when a voucher is not found."""

    def __init__(self, voucher_id: UUID) -> None:
        self.voucher_id = voucher_id
        self.message = f"Voucher {voucher_id} not found."
        super().__init__(self.message)


class VoucherCodeNotFoundError(Exception):
    """Raised when a voucher code is not found."""

    def __init__(self, code: str) -> None:
        self.code = code
        self.message = f"Voucher with code '{code}' not found."
        super().__init__(self.message)


class InvalidVoucherTransitionError(Exception):
    """Raised when a voucher status transition is not allowed."""

    def __init__(self, current: str, requested: str) -> None:
        self.current = current
        self.requested = requested
        allowed = VALID_VOUCHER_TRANSITIONS.get(current, set())
        self.message = (
            f"Cannot transition voucher from '{current}' to '{requested}'. "
            f"Allowed: {', '.join(sorted(allowed)) if allowed else 'none (terminal state)'}."
        )
        super().__init__(self.message)


class VoucherExpiredError(Exception):
    """Raised when attempting to use an expired voucher."""

    def __init__(self, voucher_id: UUID) -> None:
        self.voucher_id = voucher_id
        self.message = f"Voucher {voucher_id} has expired."
        super().__init__(self.message)


def generate_voucher_code() -> str:
    """Generate a human-readable voucher code like VV-A1B2C3D4."""
    random_part = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(VOUCHER_CODE_LENGTH))
    return f"VV-{random_part}"


async def create_voucher(db: AsyncSession, data: dict) -> VetVoucher:
    """Create a new voucher with a unique code."""
    code = generate_voucher_code()
    voucher = VetVoucher(code=code, **data)
    db.add(voucher)
    await db.flush()
    await db.refresh(voucher)
    logger.info("Created voucher %s (code=%s, amount=%d PYG)", voucher.id, code, voucher.amount_pyg)
    return voucher


async def get_voucher(db: AsyncSession, voucher_id: UUID) -> VetVoucher:
    """Fetch a voucher by ID. Raises VoucherNotFoundError if missing."""
    voucher = await db.get(VetVoucher, voucher_id)
    if voucher is None:
        raise VoucherNotFoundError(voucher_id)
    return voucher


async def get_voucher_by_code(db: AsyncSession, code: str) -> VetVoucher:
    """Fetch a voucher by its human-readable code."""
    result = await db.execute(select(VetVoucher).where(VetVoucher.code == code))
    voucher = result.scalar_one_or_none()
    if voucher is None:
        raise VoucherCodeNotFoundError(code)
    return voucher


async def list_vouchers(
    db: AsyncSession,
    *,
    status: str | None = None,
    donor_id: UUID | None = None,
    beneficiary_id: UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[VetVoucher], int]:
    """List vouchers with optional filters and pagination."""
    query = select(VetVoucher)
    count_query = select(func.count(VetVoucher.id))

    if status:
        query = query.where(VetVoucher.status == status)
        count_query = count_query.where(VetVoucher.status == status)
    if donor_id:
        query = query.where(VetVoucher.donor_id == donor_id)
        count_query = count_query.where(VetVoucher.donor_id == donor_id)
    if beneficiary_id:
        query = query.where(VetVoucher.beneficiary_id == beneficiary_id)
        count_query = count_query.where(VetVoucher.beneficiary_id == beneficiary_id)

    query = (
        query.order_by(VetVoucher.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )

    result = await db.execute(query)
    vouchers = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return vouchers, total


def _check_transition(voucher: VetVoucher, target_status: str) -> None:
    """Validate a status transition. Raises InvalidVoucherTransitionError if invalid."""
    allowed = VALID_VOUCHER_TRANSITIONS.get(voucher.status, set())
    if target_status not in allowed:
        raise InvalidVoucherTransitionError(voucher.status, target_status)


def _check_not_expired(voucher: VetVoucher) -> None:
    """Raise VoucherExpiredError if the voucher has passed its expiry date."""
    if datetime.now(UTC) > voucher.expires_at:
        raise VoucherExpiredError(voucher.id)


async def assign_voucher(db: AsyncSession, voucher_id: UUID, beneficiary_id: UUID) -> VetVoucher:
    """Assign a purchased voucher to a beneficiary (rescuer/user)."""
    voucher = await get_voucher(db, voucher_id)
    _check_transition(voucher, VoucherStatus.ASSIGNED)
    _check_not_expired(voucher)

    voucher.status = VoucherStatus.ASSIGNED
    voucher.beneficiary_id = beneficiary_id
    voucher.assigned_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(voucher)
    logger.info("Voucher %s assigned to user %s", voucher_id, beneficiary_id)
    return voucher


async def redeem_voucher(
    db: AsyncSession,
    voucher_id: UUID,
    clinic_id: UUID,
    service_id: UUID | None = None,
) -> VetVoucher:
    """Redeem a voucher at a clinic for a specific service."""
    voucher = await get_voucher(db, voucher_id)
    _check_transition(voucher, VoucherStatus.REDEEMED)
    _check_not_expired(voucher)

    # If voucher is restricted to a specific clinic, verify match
    if voucher.clinic_id is not None and voucher.clinic_id != clinic_id:
        raise InvalidVoucherTransitionError(
            voucher.status,
            f"redeemed (restricted to clinic {voucher.clinic_id})",
        )

    voucher.status = VoucherStatus.REDEEMED
    voucher.redeemed_clinic_id = clinic_id
    voucher.service_id = service_id
    voucher.redeemed_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(voucher)
    logger.info("Voucher %s redeemed at clinic %s", voucher_id, clinic_id)
    return voucher


async def cancel_voucher(db: AsyncSession, voucher_id: UUID, reason: str) -> VetVoucher:
    """Cancel a voucher with a reason."""
    voucher = await get_voucher(db, voucher_id)
    _check_transition(voucher, VoucherStatus.CANCELLED)

    voucher.status = VoucherStatus.CANCELLED
    voucher.cancellation_reason = reason
    voucher.cancelled_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(voucher)
    logger.info("Voucher %s cancelled: %s", voucher_id, reason)
    return voucher


async def expire_voucher(db: AsyncSession, voucher_id: UUID) -> VetVoucher:
    """Mark a voucher as expired."""
    voucher = await get_voucher(db, voucher_id)
    _check_transition(voucher, VoucherStatus.EXPIRED)

    voucher.status = VoucherStatus.EXPIRED

    await db.flush()
    await db.refresh(voucher)
    logger.info("Voucher %s expired", voucher_id)
    return voucher
