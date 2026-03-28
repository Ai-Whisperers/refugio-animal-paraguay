"""Emergency case service — creation and management of urgent rescue cases.

Creates emergency cases with linked fundraising campaigns. Handles
validation, status transitions, and deadline enforcement.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.campaign import Campaign
from src.db.models.emergency_case import EmergencyCase

logger = logging.getLogger(__name__)

# Configuration
MIN_DEADLINE_HOURS = 24
MAX_DEADLINE_DAYS = 30
TITLE_MAX_LENGTH = 200

VALID_STATUSES = frozenset({"active", "funded", "closed", "expired"})
VALID_URGENCY = frozenset({"high", "critical"})
VALID_CURRENCIES = frozenset({"USD", "PYG"})


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class EmergencyError(Exception):
    """Base error for emergency operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class EmergencyNotFoundError(EmergencyError):
    """Raised when emergency case not found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(
            message="Emergency case not found",
            details=f"No emergency case found for: {identifier}",
        )


class InvalidDeadlineError(EmergencyError):
    """Raised when deadline is invalid."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            message="Invalid deadline",
            details=reason,
        )


class InvalidStatusTransitionError(EmergencyError):
    """Raised for invalid status transition."""

    def __init__(self, current: str, target: str) -> None:
        super().__init__(
            message="Invalid status transition",
            details=f"Cannot transition from '{current}' to '{target}'",
        )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

# Valid status transitions
_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "active": {"funded", "closed", "expired"},
    "funded": {"closed"},
    "closed": set(),
    "expired": set(),
}


def validate_deadline(deadline: datetime) -> None:
    """Validate that deadline is at least 24h and at most 30d from now."""
    now = datetime.now(UTC)
    min_deadline = now + timedelta(hours=MIN_DEADLINE_HOURS)
    max_deadline = now + timedelta(days=MAX_DEADLINE_DAYS)

    if deadline < min_deadline:
        raise InvalidDeadlineError(f"Deadline must be at least {MIN_DEADLINE_HOURS} hours from now")
    if deadline > max_deadline:
        raise InvalidDeadlineError(f"Deadline must be at most {MAX_DEADLINE_DAYS} days from now")


def validate_status_transition(current: str, target: str) -> None:
    """Validate a status transition is allowed."""
    allowed = _STATUS_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStatusTransitionError(current, target)


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def create_emergency_case(
    *,
    title: str,
    description: str,
    rescuer_id: UUID,
    amount_needed_cents: int,
    deadline: datetime,
    animal_id: UUID | None = None,
    photos: list | None = None,
    currency: str = "USD",
    urgency: str = "high",
    db: AsyncSession,
) -> EmergencyCase:
    """Create an emergency case and its linked fundraising campaign.

    Both are created in the same flush to ensure atomicity.

    Raises:
        InvalidDeadlineError: If deadline is out of range.
        EmergencyError: If validation fails.
    """
    # Validate inputs
    if len(title) > TITLE_MAX_LENGTH:
        raise EmergencyError(
            "Title too long",
            details=f"Title must be at most {TITLE_MAX_LENGTH} characters",
        )
    if amount_needed_cents <= 0:
        raise EmergencyError(
            "Invalid amount",
            details="Amount must be greater than zero",
        )
    if currency not in VALID_CURRENCIES:
        raise EmergencyError(
            "Invalid currency",
            details=f"Must be one of: {', '.join(sorted(VALID_CURRENCIES))}",
        )
    if urgency not in VALID_URGENCY:
        raise EmergencyError(
            "Invalid urgency",
            details=f"Must be one of: {', '.join(sorted(VALID_URGENCY))}",
        )

    validate_deadline(deadline)

    # Create linked campaign
    campaign = Campaign(
        title=f"[EMERGENCY] {title}",
        description=description,
        target_amount_cents=amount_needed_cents,
        currency=currency,
        deadline=deadline,
        status="active",
        fund_category="rescue",
        is_emergency=True,
        created_by_id=rescuer_id,
    )
    db.add(campaign)
    await db.flush()  # Get campaign.id

    # Create emergency case
    case = EmergencyCase(
        title=title,
        description=description,
        animal_id=animal_id,
        rescuer_id=rescuer_id,
        campaign_id=campaign.id,
        photos=photos or [],
        amount_needed_cents=amount_needed_cents,
        amount_raised_cents=0,
        currency=currency,
        deadline=deadline,
        urgency=urgency,
    )
    db.add(case)
    await db.flush()

    logger.info(
        "Emergency case created: id=%s campaign=%s rescuer=%s urgency=%s",
        case.id,
        campaign.id,
        rescuer_id,
        urgency,
    )
    return case


async def get_emergency_case(
    emergency_id: UUID,
    db: AsyncSession,
) -> EmergencyCase:
    """Get an emergency case by ID.

    Raises:
        EmergencyNotFoundError: If not found or soft-deleted.
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
    return case


async def update_emergency_status(
    *,
    emergency_id: UUID,
    new_status: str,
    db: AsyncSession,
) -> EmergencyCase:
    """Update the status of an emergency case.

    Raises:
        EmergencyNotFoundError: If not found.
        InvalidStatusTransitionError: If transition is not allowed.
    """
    case = await get_emergency_case(emergency_id, db)
    validate_status_transition(case.status, new_status)

    case.status = new_status
    await db.flush()

    logger.info(
        "Emergency status updated: id=%s status=%s",
        emergency_id,
        new_status,
    )
    return case


async def soft_delete_emergency(
    *,
    emergency_id: UUID,
    db: AsyncSession,
) -> EmergencyCase:
    """Soft-delete an emergency case.

    Raises:
        EmergencyNotFoundError: If not found.
    """
    case = await get_emergency_case(emergency_id, db)
    case.is_deleted = True
    await db.flush()

    logger.info("Emergency soft-deleted: id=%s", emergency_id)
    return case


async def list_active_emergencies(
    db: AsyncSession,
    *,
    urgency: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[EmergencyCase]:
    """List active (non-deleted, non-expired) emergency cases."""
    query = (
        select(EmergencyCase)
        .where(
            EmergencyCase.is_deleted.is_(False),
            EmergencyCase.status.in_(["active", "funded"]),
        )
        .order_by(EmergencyCase.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if urgency:
        query = query.where(EmergencyCase.urgency == urgency)

    result = await db.execute(query)
    return list(result.scalars().all())
