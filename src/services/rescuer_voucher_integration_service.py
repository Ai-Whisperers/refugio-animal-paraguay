"""Rescuer-voucher integration service — connects rescuer profiles to vet vouchers.

Provides rescuer-specific voucher operations: requesting vouchers for animals
under their care, viewing voucher usage statistics, and generating voucher
eligibility checks based on rescuer verification status.
"""

import logging
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.rescuer_profile import RescuerProfile
from src.db.models.vet_voucher import VetVoucher, VoucherStatus

logger = logging.getLogger(__name__)

# Voucher request constraints
MAX_ACTIVE_VOUCHER_REQUESTS = 10
MAX_REQUEST_NOTES_LENGTH = 1000
VERIFIED_RESCUER_VOUCHER_LIMIT = 20
UNVERIFIED_RESCUER_VOUCHER_LIMIT = 5

VALID_SERVICE_CATEGORIES = frozenset(
    {
        "vaccination",
        "sterilization",
        "consultation",
        "emergency",
        "surgery",
        "dental",
        "deworming",
        "general",
    }
)


class RescuerVoucherError(Exception):
    """Base error for rescuer-voucher integration operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class RescuerProfileRequiredError(RescuerVoucherError):
    """Raised when the user has no rescuer profile."""

    def __init__(self, user_id: UUID) -> None:
        super().__init__(
            message="Rescuer profile required",
            details=f"User {user_id} must register as a rescuer first",
        )


class VerificationRequiredError(RescuerVoucherError):
    """Raised when the operation requires a verified rescuer."""

    def __init__(self) -> None:
        super().__init__(
            message="Verification required",
            details="This operation is only available to verified rescuers",
        )


class VoucherLimitExceededError(RescuerVoucherError):
    """Raised when the rescuer has exceeded their voucher limit."""

    def __init__(self, limit: int) -> None:
        super().__init__(
            message="Voucher limit exceeded",
            details=f"Maximum {limit} active vouchers allowed",
        )


class InvalidServiceCategoryError(RescuerVoucherError):
    """Raised when an invalid service category is provided."""

    def __init__(self, category: str) -> None:
        super().__init__(
            message="Invalid service category",
            details=f"Category '{category}' is not valid. Valid: {', '.join(sorted(VALID_SERVICE_CATEGORIES))}",
        )


def validate_service_category(category: str | None) -> None:
    """Validate the service category if provided."""
    if category and category not in VALID_SERVICE_CATEGORIES:
        raise InvalidServiceCategoryError(category)


def validate_request_notes(notes: str | None) -> None:
    """Validate request notes length."""
    if notes and len(notes) > MAX_REQUEST_NOTES_LENGTH:
        raise RescuerVoucherError(
            message="Notes too long",
            details=f"Maximum {MAX_REQUEST_NOTES_LENGTH} characters allowed",
        )


async def _get_rescuer_profile(db: AsyncSession, user_id: UUID) -> RescuerProfile:
    """Look up the rescuer profile for a user. Raises if not found."""
    result = await db.execute(select(RescuerProfile).where(RescuerProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise RescuerProfileRequiredError(user_id)
    return profile


async def _count_active_vouchers(db: AsyncSession, beneficiary_id: UUID) -> int:
    """Count vouchers in active states (purchased, assigned) for a beneficiary."""
    result = await db.execute(
        select(func.count(VetVoucher.id)).where(
            and_(
                VetVoucher.beneficiary_id == beneficiary_id,
                VetVoucher.status.in_([VoucherStatus.PURCHASED, VoucherStatus.ASSIGNED]),
            )
        )
    )
    return result.scalar_one()


async def get_rescuer_voucher_eligibility(
    user_id: UUID,
    db: AsyncSession,
) -> dict:
    """Check a rescuer's voucher eligibility and current usage.

    Returns eligibility information including whether they can request
    more vouchers, their limits, and current usage.

    Raises:
        RescuerProfileRequiredError: If user has no rescuer profile.
    """
    profile = await _get_rescuer_profile(db, user_id)

    voucher_limit = (
        VERIFIED_RESCUER_VOUCHER_LIMIT if profile.is_verified else UNVERIFIED_RESCUER_VOUCHER_LIMIT
    )

    active_count = await _count_active_vouchers(db, user_id)

    # Count redeemed vouchers (lifetime)
    redeemed_result = await db.execute(
        select(func.count(VetVoucher.id)).where(
            and_(
                VetVoucher.beneficiary_id == user_id,
                VetVoucher.status == VoucherStatus.REDEEMED,
            )
        )
    )
    redeemed_count = redeemed_result.scalar_one()

    # Total value of redeemed vouchers
    value_result = await db.execute(
        select(func.coalesce(func.sum(VetVoucher.amount_pyg), 0)).where(
            and_(
                VetVoucher.beneficiary_id == user_id,
                VetVoucher.status == VoucherStatus.REDEEMED,
            )
        )
    )
    total_redeemed_pyg = value_result.scalar_one()

    return {
        "rescuer_profile_id": str(profile.id),
        "is_verified": profile.is_verified,
        "voucher_limit": voucher_limit,
        "active_vouchers": active_count,
        "remaining_slots": max(0, voucher_limit - active_count),
        "can_request_more": active_count < voucher_limit,
        "lifetime_redeemed": redeemed_count,
        "lifetime_redeemed_pyg": total_redeemed_pyg,
    }


async def get_rescuer_voucher_history(
    user_id: UUID,
    db: AsyncSession,
    *,
    status_filter: str | None = None,
    service_category: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[VetVoucher]:
    """Get voucher history for a rescuer, with optional filters.

    Raises:
        RescuerProfileRequiredError: If user has no rescuer profile.
    """
    # Verify rescuer exists
    await _get_rescuer_profile(db, user_id)

    query = select(VetVoucher).where(VetVoucher.beneficiary_id == user_id)

    if status_filter:
        query = query.where(VetVoucher.status == status_filter)
    if service_category:
        validate_service_category(service_category)
        query = query.where(VetVoucher.service_category == service_category)

    query = query.order_by(VetVoucher.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_rescuer_voucher_stats(
    user_id: UUID,
    db: AsyncSession,
) -> dict:
    """Get aggregate voucher statistics for a rescuer.

    Returns counts and values by status and service category.

    Raises:
        RescuerProfileRequiredError: If user has no rescuer profile.
    """
    profile = await _get_rescuer_profile(db, user_id)

    # Count by status
    status_counts_result = await db.execute(
        select(VetVoucher.status, func.count(VetVoucher.id))
        .where(VetVoucher.beneficiary_id == user_id)
        .group_by(VetVoucher.status)
    )
    status_counts = {row[0]: row[1] for row in status_counts_result.all()}

    # Total value by status
    status_values_result = await db.execute(
        select(
            VetVoucher.status,
            func.coalesce(func.sum(VetVoucher.amount_pyg), 0),
        )
        .where(VetVoucher.beneficiary_id == user_id)
        .group_by(VetVoucher.status)
    )
    status_values = {row[0]: row[1] for row in status_values_result.all()}

    # Count by service category (redeemed only)
    category_counts_result = await db.execute(
        select(
            VetVoucher.service_category,
            func.count(VetVoucher.id),
        )
        .where(
            and_(
                VetVoucher.beneficiary_id == user_id,
                VetVoucher.status == VoucherStatus.REDEEMED,
                VetVoucher.service_category.is_not(None),
            )
        )
        .group_by(VetVoucher.service_category)
    )
    category_counts = {row[0]: row[1] for row in category_counts_result.all()}

    return {
        "rescuer_profile_id": str(profile.id),
        "is_verified": profile.is_verified,
        "by_status": {
            "counts": status_counts,
            "values_pyg": status_values,
        },
        "by_category": category_counts,
        "total_vouchers": sum(status_counts.values()),
        "total_value_pyg": sum(status_values.values()),
    }


async def check_voucher_request_eligibility(
    user_id: UUID,
    service_category: str | None,
    db: AsyncSession,
) -> dict:
    """Pre-check whether a rescuer can request a voucher.

    Validates rescuer profile, verification status, and voucher limits.

    Raises:
        RescuerProfileRequiredError: If user has no rescuer profile.
        VoucherLimitExceededError: If voucher limit reached.
        InvalidServiceCategoryError: If category is invalid.
    """
    validate_service_category(service_category)

    profile = await _get_rescuer_profile(db, user_id)

    voucher_limit = (
        VERIFIED_RESCUER_VOUCHER_LIMIT if profile.is_verified else UNVERIFIED_RESCUER_VOUCHER_LIMIT
    )

    active_count = await _count_active_vouchers(db, user_id)
    if active_count >= voucher_limit:
        raise VoucherLimitExceededError(voucher_limit)

    return {
        "eligible": True,
        "rescuer_profile_id": str(profile.id),
        "is_verified": profile.is_verified,
        "remaining_slots": voucher_limit - active_count,
        "service_category": service_category,
    }
