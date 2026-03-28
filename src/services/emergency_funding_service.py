"""Emergency funding service — monitors and auto-closes funded emergencies.

Checks emergency cases against their funding targets and automatically
transitions fully funded cases from 'active' to 'funded' status. Also
handles expiry of past-deadline cases.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.emergency_case import EmergencyCase

logger = logging.getLogger(__name__)

# Configuration
FUNDING_THRESHOLD_PCT = 100


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class FundingCheckError(Exception):
    """Base error for funding check operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class EmergencyNotFoundError(FundingCheckError):
    """Raised when emergency case not found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(
            message="Emergency case not found",
            details=f"No active emergency case found for: {identifier}",
        )


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


async def check_and_update_funding(
    *,
    emergency_id: UUID,
    db: AsyncSession,
) -> dict:
    """Check if an emergency case is fully funded and update status.

    Returns a dict with the check result:
        - emergency_id: UUID of the case
        - previous_status: status before check
        - new_status: status after check (may be unchanged)
        - amount_needed_cents: target amount
        - amount_raised_cents: current raised amount
        - is_funded: whether the case is now fully funded
        - action_taken: description of what happened

    Raises:
        EmergencyNotFoundError: If case not found or already closed.
    """
    result = await db.execute(
        select(EmergencyCase).where(
            EmergencyCase.id == emergency_id,
            EmergencyCase.is_deleted.is_(False),
        )
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise EmergencyNotFoundError(str(emergency_id))

    previous_status = case.status
    is_funded = case.amount_raised_cents >= case.amount_needed_cents
    action_taken = "no_change"

    if case.status == "active" and is_funded:
        case.status = "funded"
        action_taken = "status_changed_to_funded"
        await db.flush()
        logger.info(
            "Emergency auto-funded: id=%s raised=%d needed=%d",
            emergency_id,
            case.amount_raised_cents,
            case.amount_needed_cents,
        )

    return {
        "emergency_id": case.id,
        "previous_status": previous_status,
        "new_status": case.status,
        "amount_needed_cents": case.amount_needed_cents,
        "amount_raised_cents": case.amount_raised_cents,
        "is_funded": is_funded,
        "action_taken": action_taken,
    }


async def process_donation_for_emergency(
    *,
    emergency_id: UUID,
    donation_amount_cents: int,
    db: AsyncSession,
) -> dict:
    """Record a donation amount and check funding status.

    Increments amount_raised_cents and checks if the emergency
    is now fully funded.

    Returns the same dict as check_and_update_funding.

    Raises:
        EmergencyNotFoundError: If case not found.
        FundingCheckError: If donation amount is invalid.
    """
    if donation_amount_cents <= 0:
        raise FundingCheckError(
            "Invalid donation amount",
            details="Donation amount must be greater than zero",
        )

    result = await db.execute(
        select(EmergencyCase).where(
            EmergencyCase.id == emergency_id,
            EmergencyCase.is_deleted.is_(False),
        )
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise EmergencyNotFoundError(str(emergency_id))

    if case.status not in ("active", "funded"):
        raise FundingCheckError(
            "Emergency not accepting donations",
            details=f"Emergency is in '{case.status}' status",
        )

    # Increment raised amount
    case.amount_raised_cents = case.amount_raised_cents + donation_amount_cents
    await db.flush()

    logger.info(
        "Donation recorded for emergency: id=%s amount=%d total_raised=%d",
        emergency_id,
        donation_amount_cents,
        case.amount_raised_cents,
    )

    # Check if now funded
    return await check_and_update_funding(
        emergency_id=emergency_id,
        db=db,
    )


async def batch_check_active_emergencies(
    db: AsyncSession,
) -> list[dict]:
    """Check all active emergencies for funding completion and expiry.

    Processes two categories:
    1. Active cases that are now fully funded -> mark as 'funded'
    2. Active cases past their deadline -> mark as 'expired'

    Returns a list of result dicts for cases that were updated.
    """
    now = datetime.now(UTC)
    results: list[dict] = []

    # Find active emergencies that are fully funded
    funded_result = await db.execute(
        select(EmergencyCase).where(
            EmergencyCase.is_deleted.is_(False),
            EmergencyCase.status == "active",
            EmergencyCase.amount_raised_cents >= EmergencyCase.amount_needed_cents,
        )
    )
    funded_cases = list(funded_result.scalars().all())

    for case in funded_cases:
        case.status = "funded"
        results.append(
            {
                "emergency_id": case.id,
                "previous_status": "active",
                "new_status": "funded",
                "action_taken": "batch_funded",
                "amount_needed_cents": case.amount_needed_cents,
                "amount_raised_cents": case.amount_raised_cents,
            }
        )
        logger.info("Batch auto-funded emergency: id=%s", case.id)

    # Find active emergencies past their deadline
    expired_result = await db.execute(
        select(EmergencyCase).where(
            EmergencyCase.is_deleted.is_(False),
            EmergencyCase.status == "active",
            EmergencyCase.deadline < now,
        )
    )
    expired_cases = list(expired_result.scalars().all())

    for case in expired_cases:
        case.status = "expired"
        results.append(
            {
                "emergency_id": case.id,
                "previous_status": "active",
                "new_status": "expired",
                "action_taken": "batch_expired",
                "amount_needed_cents": case.amount_needed_cents,
                "amount_raised_cents": case.amount_raised_cents,
            }
        )
        logger.info("Batch expired emergency: id=%s", case.id)

    if results:
        await db.flush()
        logger.info(
            "Batch check complete: %d funded, %d expired",
            len(funded_cases),
            len(expired_cases),
        )

    return results


async def get_funding_progress(
    *,
    emergency_id: UUID,
    db: AsyncSession,
) -> dict:
    """Get funding progress for an emergency case.

    Returns:
        Dict with funding details including percentage and remaining amount.

    Raises:
        EmergencyNotFoundError: If case not found.
    """
    result = await db.execute(
        select(EmergencyCase).where(
            EmergencyCase.id == emergency_id,
            EmergencyCase.is_deleted.is_(False),
        )
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise EmergencyNotFoundError(str(emergency_id))

    needed = case.amount_needed_cents
    raised = case.amount_raised_cents
    remaining = max(0, needed - raised)
    pct = min(100, round((raised / needed) * 100, 1)) if needed > 0 else 0

    return {
        "emergency_id": case.id,
        "status": case.status,
        "amount_needed_cents": needed,
        "amount_raised_cents": raised,
        "amount_remaining_cents": remaining,
        "funding_percentage": pct,
        "is_fully_funded": raised >= needed,
        "currency": case.currency,
        "deadline": case.deadline.isoformat() if case.deadline else None,
    }
