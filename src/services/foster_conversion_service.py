"""Foster-to-adopt conversion service (RAP-193).

When a foster family decides to permanently adopt the animal they are fostering,
staff can use this service to convert the active placement into a formal, pre-approved
adoption request.  The workflow:

  1. Validate the placement is active (ended_at is None).
  2. Resolve or create an Adopter record for the foster family's user.
  3. Create an AdoptionRequest with status APPROVED (staff-initiated fast-track).
  4. Close the FosterPlacement by setting ended_at = now().
  5. Update the Animal status to ADOPTED.

All five steps happen inside a single DB transaction — either all succeed or none do.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.db.models.animal import Animal, AnimalStatus
from src.db.models.foster_placement import FosterPlacement
from src.db.models.foster_profile import FosterProfile
from src.db.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class FosterConversionResult:
    """Outcome of a successful foster-to-adopt conversion."""

    placement_id: UUID
    adoption_request_id: UUID
    adopter_id: UUID
    animal_id: UUID
    foster_profile_id: UUID
    adopter_created: bool  # True when a new Adopter record was auto-created
    converted_at: datetime


# ---------------------------------------------------------------------------
# Public service function
# ---------------------------------------------------------------------------


async def convert_foster_to_adoption(
    db: AsyncSession,
    placement_id: UUID,
    staff_notes: str | None = None,
) -> FosterConversionResult:
    """Convert an active foster placement into an approved adoption request.

    Raises:
        ValueError: with a descriptive message when:
            - The placement does not exist (message contains "not found").
            - The placement is already closed (message contains "already closed").
            - The foster profile is missing (message contains "foster profile").
            - The foster user is missing (message contains "user").
    """
    now = datetime.now(tz=UTC)

    # 1. Load the placement and verify it is active -------------------------
    result = await db.execute(select(FosterPlacement).where(FosterPlacement.id == placement_id))
    placement: FosterPlacement | None = result.scalar_one_or_none()

    if placement is None:
        raise ValueError(f"Foster placement {placement_id} not found")

    if placement.ended_at is not None:
        raise ValueError(
            f"Foster placement {placement_id} is already closed "
            f"(ended at {placement.ended_at.isoformat()})"
        )

    # 2. Load the foster profile to get the user_id -------------------------
    profile_result = await db.execute(
        select(FosterProfile).where(FosterProfile.id == placement.foster_profile_id)
    )
    profile: FosterProfile | None = profile_result.scalar_one_or_none()
    if profile is None:
        raise ValueError(
            f"Foster profile {placement.foster_profile_id} not found — data integrity error"
        )

    # 3. Load the user to obtain name / email for adopter record ------------
    user_result = await db.execute(select(User).where(User.id == profile.user_id))
    user: User | None = user_result.scalar_one_or_none()
    if user is None:
        raise ValueError(
            f"User {profile.user_id} linked to foster profile not found — data integrity error"
        )

    # 4. Resolve or create an Adopter record --------------------------------
    adopter_result = await db.execute(select(Adopter).where(Adopter.email == user.email))
    adopter: Adopter | None = adopter_result.scalar_one_or_none()
    adopter_created = False

    if adopter is None:
        # Auto-create a minimal adopter record so the adoption request can be persisted.
        # Staff can enrich the record later through the adopter management interface.
        adopter = Adopter(
            full_name=user.full_name or user.email.split("@")[0],
            email=user.email,
            phone=user.phone,
        )
        db.add(adopter)
        await db.flush()  # obtain the generated UUID before using it below
        adopter_created = True
        logger.info(
            "Auto-created adopter record during foster-to-adopt conversion",
            extra={"user_id": str(user.id), "adopter_id": str(adopter.id)},
        )

    # 5. Load the animal to update its status --------------------------------
    animal_result = await db.execute(select(Animal).where(Animal.id == placement.animal_id))
    animal: Animal | None = animal_result.scalar_one_or_none()
    if animal is None:
        raise ValueError(
            f"Animal {placement.animal_id} linked to placement not found — data integrity error"
        )

    # 6. Create an APPROVED adoption request (fast-track — staff initiated) --
    conversion_note = "Converted from foster placement"
    if staff_notes:
        conversion_note = f"{conversion_note}. {staff_notes}"

    adoption_request = AdoptionRequest(
        animal_id=placement.animal_id,
        adopter_id=adopter.id,
        status=AdoptionRequestStatus.APPROVED,
        submitted_at=now,
        decided_at=now,
        notes=conversion_note,
    )
    db.add(adoption_request)
    await db.flush()

    # 7. Close the foster placement -----------------------------------------
    placement.ended_at = now
    if staff_notes:
        existing_notes = placement.notes or ""
        sep = "\n" if existing_notes else ""
        placement.notes = f"{existing_notes}{sep}Converted to adoption: {staff_notes}"

    # 8. Update the animal status -------------------------------------------
    animal.status = AnimalStatus.ADOPTED

    await db.commit()
    await db.refresh(adoption_request)
    await db.refresh(placement)
    await db.refresh(animal)

    logger.info(
        "Foster-to-adopt conversion completed",
        extra={
            "placement_id": str(placement_id),
            "adoption_request_id": str(adoption_request.id),
            "adopter_id": str(adopter.id),
            "animal_id": str(animal.id),
            "adopter_created": adopter_created,
        },
    )

    return FosterConversionResult(
        placement_id=placement_id,
        adoption_request_id=adoption_request.id,
        adopter_id=adopter.id,
        animal_id=placement.animal_id,
        foster_profile_id=placement.foster_profile_id,
        adopter_created=adopter_created,
        converted_at=now,
    )
