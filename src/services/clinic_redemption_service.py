"""Service for clinic voucher redemption workflow.

Handles voucher lookup by code, redemption with proof-of-service,
and listing vouchers by clinic for reconciliation.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.vet_voucher import VetVoucher, VoucherStatus
from src.services.vet_voucher_service import (
    _check_not_expired,
    _check_transition,
    get_voucher_by_code,
)

logger = logging.getLogger(__name__)


class VoucherNotAssignedError(Exception):
    """Raised when trying to redeem a voucher that has not been assigned."""

    def __init__(self, code: str, status: str) -> None:
        self.code = code
        self.status = status
        self.message = (
            f"Voucher '{code}' cannot be redeemed — current status is '{status}'. "
            f"Only assigned vouchers can be redeemed."
        )
        super().__init__(self.message)


class VoucherClinicMismatchError(Exception):
    """Raised when a clinic-restricted voucher is redeemed at the wrong clinic."""

    def __init__(self, code: str, restricted_clinic_id: UUID, attempted_clinic_id: UUID) -> None:
        self.code = code
        self.restricted_clinic_id = restricted_clinic_id
        self.attempted_clinic_id = attempted_clinic_id
        self.message = (
            f"Voucher '{code}' is restricted to clinic {restricted_clinic_id} "
            f"but attempted at clinic {attempted_clinic_id}."
        )
        super().__init__(self.message)


async def lookup_voucher_for_redemption(db: AsyncSession, code: str) -> VetVoucher:
    """Look up a voucher by code and validate it is ready for redemption.

    Returns the voucher if it exists and is in a redeemable state (assigned).
    Raises appropriate errors for not-found, wrong status, or expired.
    """
    voucher = await get_voucher_by_code(db, code)

    if voucher.status != VoucherStatus.ASSIGNED:
        raise VoucherNotAssignedError(code, voucher.status)

    _check_not_expired(voucher)
    return voucher


async def redeem_voucher_at_clinic(
    db: AsyncSession,
    code: str,
    *,
    clinic_id: UUID,
    redeemed_by_user_id: UUID,
    service_id: UUID | None = None,
    proof_photo_url: str | None = None,
    proof_description: str | None = None,
    invoice_url: str | None = None,
    invoice_filename: str | None = None,
) -> VetVoucher:
    """Redeem a voucher at a clinic with proof of service.

    Validates the voucher is assigned and not expired, checks clinic restriction,
    records proof details, and transitions to redeemed status.
    """
    voucher = await get_voucher_by_code(db, code)

    _check_transition(voucher, VoucherStatus.REDEEMED)
    _check_not_expired(voucher)

    # Enforce clinic restriction if set
    if voucher.clinic_id is not None and voucher.clinic_id != clinic_id:
        raise VoucherClinicMismatchError(code, voucher.clinic_id, clinic_id)

    now = datetime.now(UTC)
    voucher.status = VoucherStatus.REDEEMED
    voucher.redeemed_clinic_id = clinic_id
    voucher.redeemed_by_user_id = redeemed_by_user_id
    voucher.service_id = service_id
    voucher.redeemed_at = now
    voucher.proof_photo_url = proof_photo_url
    voucher.proof_description = proof_description
    voucher.invoice_url = invoice_url
    voucher.invoice_filename = invoice_filename

    await db.flush()
    await db.refresh(voucher)

    logger.info(
        "Voucher %s (code=%s) redeemed at clinic %s by user %s",
        voucher.id,
        code,
        clinic_id,
        redeemed_by_user_id,
    )
    return voucher


async def list_clinic_vouchers(
    db: AsyncSession,
    clinic_id: UUID,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[VetVoucher], int]:
    """List vouchers associated with a clinic (restricted or redeemed there).

    Returns vouchers either restricted to this clinic or redeemed at this clinic.
    """
    query = select(VetVoucher).where(
        (VetVoucher.clinic_id == clinic_id) | (VetVoucher.redeemed_clinic_id == clinic_id)
    )
    count_query = select(func.count(VetVoucher.id)).where(
        (VetVoucher.clinic_id == clinic_id) | (VetVoucher.redeemed_clinic_id == clinic_id)
    )

    if status:
        query = query.where(VetVoucher.status == status)
        count_query = count_query.where(VetVoucher.status == status)

    query = (
        query.order_by(VetVoucher.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )

    result = await db.execute(query)
    vouchers = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return vouchers, total


async def get_clinic_reconciliation_summary(
    db: AsyncSession,
    clinic_id: UUID,
    *,
    month: int | None = None,
    year: int | None = None,
) -> dict:
    """Get reconciliation summary for a clinic.

    Returns total redeemed count and amount for a given month/year.
    Defaults to current month if not specified.
    """
    now = datetime.now(UTC)
    target_month = month or now.month
    target_year = year or now.year

    query = select(
        func.count(VetVoucher.id).label("total_redeemed"),
        func.coalesce(func.sum(VetVoucher.amount_pyg), 0).label("total_amount_pyg"),
    ).where(
        VetVoucher.redeemed_clinic_id == clinic_id,
        VetVoucher.status == VoucherStatus.REDEEMED,
        func.extract("month", VetVoucher.redeemed_at) == target_month,
        func.extract("year", VetVoucher.redeemed_at) == target_year,
    )

    result = await db.execute(query)
    row = result.one()

    return {
        "clinic_id": str(clinic_id),
        "month": target_month,
        "year": target_year,
        "total_redeemed": row.total_redeemed,
        "total_amount_pyg": row.total_amount_pyg,
    }
