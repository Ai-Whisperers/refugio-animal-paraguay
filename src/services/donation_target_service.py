"""Service for validating and resolving donation target types.

Handles validation that a donation target exists and is active/available
before accepting a directed donation.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.animal import Animal, AnimalStatus
from src.db.models.donation import DonationTargetType

logger = logging.getLogger(__name__)

# Target types that require a target_id
DIRECTED_TARGET_TYPES = frozenset(
    {
        DonationTargetType.ANIMAL,
        DonationTargetType.RESCUER,
        DonationTargetType.CLINIC,
        DonationTargetType.CAMPAIGN,
        DonationTargetType.NEED,
    }
)


class InvalidTargetError(Exception):
    """Raised when a donation target is invalid or not found."""

    def __init__(self, target_type: str, target_id: UUID | None, reason: str) -> None:
        self.target_type = target_type
        self.target_id = target_id
        self.reason = reason
        self.message = f"Invalid donation target: {reason}"
        super().__init__(self.message)


class TargetNotActiveError(Exception):
    """Raised when a donation target exists but is not accepting donations."""

    def __init__(self, target_type: str, target_id: UUID, reason: str) -> None:
        self.target_type = target_type
        self.target_id = target_id
        self.reason = reason
        self.message = f"Target not accepting donations: {reason}"
        super().__init__(self.message)


def validate_target_consistency(
    target_type: str,
    target_id: UUID | None,
) -> None:
    """Validate that target_type and target_id are consistent.

    Rules:
    - If target_type is 'general', target_id must be None
    - If target_type is not 'general', target_id must be provided
    - target_type must be a valid DonationTargetType value

    Raises InvalidTargetError if validation fails.
    """
    # Validate target_type is a known value
    valid_types = {t.value for t in DonationTargetType}
    if target_type not in valid_types:
        raise InvalidTargetError(
            target_type=target_type,
            target_id=target_id,
            reason=f"Unknown target type '{target_type}'. Valid types: {sorted(valid_types)}",
        )

    if target_type == DonationTargetType.GENERAL and target_id is not None:
        raise InvalidTargetError(
            target_type=target_type,
            target_id=target_id,
            reason="target_id must be null for 'general' donations",
        )

    if target_type != DonationTargetType.GENERAL and target_id is None:
        raise InvalidTargetError(
            target_type=target_type,
            target_id=target_id,
            reason=f"target_id is required for '{target_type}' donations",
        )


async def _validate_animal_target(db: AsyncSession, target_id: UUID) -> None:
    """Validate that an animal target exists and is available for donations."""
    animal = await db.get(Animal, target_id)
    if animal is None:
        raise InvalidTargetError(
            target_type=DonationTargetType.ANIMAL,
            target_id=target_id,
            reason=f"Animal {target_id} not found",
        )
    if animal.status == AnimalStatus.ADOPTED:
        raise TargetNotActiveError(
            target_type=DonationTargetType.ANIMAL,
            target_id=target_id,
            reason=f"Animal {target_id} has been adopted",
        )


async def _validate_campaign_target(db: AsyncSession, target_id: UUID) -> None:
    """Validate that a campaign target exists and is active."""
    from src.db.models.campaign import Campaign, CampaignStatus

    campaign = await db.get(Campaign, target_id)
    if campaign is None:
        raise InvalidTargetError(
            target_type=DonationTargetType.CAMPAIGN,
            target_id=target_id,
            reason=f"Campaign {target_id} not found",
        )
    if campaign.status != CampaignStatus.ACTIVE.value:
        raise TargetNotActiveError(
            target_type=DonationTargetType.CAMPAIGN,
            target_id=target_id,
            reason=f"Campaign {target_id} is not active (status: {campaign.status})",
        )


async def _validate_clinic_target(db: AsyncSession, target_id: UUID) -> None:
    """Validate that a vet clinic target exists."""
    from src.db.models.vet_clinic import VetClinic

    clinic = await db.get(VetClinic, target_id)
    if clinic is None:
        raise InvalidTargetError(
            target_type=DonationTargetType.CLINIC,
            target_id=target_id,
            reason=f"Clinic {target_id} not found",
        )
    from src.db.models.vet_clinic import ClinicStatus

    if clinic.status != ClinicStatus.ACTIVE:
        raise TargetNotActiveError(
            target_type=DonationTargetType.CLINIC,
            target_id=target_id,
            reason=f"Clinic {target_id} is not active (status: {clinic.status})",
        )


async def _validate_rescuer_target(db: AsyncSession, target_id: UUID) -> None:
    """Validate that a rescuer target exists.

    Note: Rescuer model may not exist yet (EPIC-80). This is a forward-looking
    validation stub that will check the users table for a user with rescuer role.
    For now, validates the UUID exists as a user.
    """
    from src.db.models.user import User

    user = await db.get(User, target_id)
    if user is None:
        raise InvalidTargetError(
            target_type=DonationTargetType.RESCUER,
            target_id=target_id,
            reason=f"Rescuer {target_id} not found",
        )


async def _validate_need_target(db: AsyncSession, target_id: UUID) -> None:
    """Validate that a need target exists.

    Note: Need model may not exist yet (EPIC-80). This is a forward-looking
    validation stub. For now, accepts any valid UUID to allow future integration.
    """
    # Needs model will be added in a future story. For now, we log a warning
    # and allow it through to avoid blocking the target type system.
    logger.warning(
        "Need target validation is a stub — need %s accepted without verification",
        target_id,
    )


# Map of target types to their validation functions
_TARGET_VALIDATORS = {
    DonationTargetType.ANIMAL: _validate_animal_target,
    DonationTargetType.CAMPAIGN: _validate_campaign_target,
    DonationTargetType.CLINIC: _validate_clinic_target,
    DonationTargetType.RESCUER: _validate_rescuer_target,
    DonationTargetType.NEED: _validate_need_target,
}


async def validate_donation_target(
    db: AsyncSession,
    target_type: str,
    target_id: UUID | None,
) -> None:
    """Validate a donation target is consistent, exists, and is active.

    This is the main entry point for target validation. Call this before
    creating a donation with a specific target.

    Raises:
        InvalidTargetError: If the target is malformed or not found
        TargetNotActiveError: If the target exists but is not accepting donations
    """
    validate_target_consistency(target_type, target_id)

    if target_type == DonationTargetType.GENERAL:
        return

    validator = _TARGET_VALIDATORS.get(DonationTargetType(target_type))
    if validator is not None and target_id is not None:
        await validator(db, target_id)
