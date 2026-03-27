"""Service layer for partner veterinary clinic management.

Handles CRUD operations, status transitions, and validation for vet clinics.
Admin/staff roles required for write operations (enforced at API layer).
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.vet_clinic import ClinicStatus, VetClinic

logger = logging.getLogger(__name__)

VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    ClinicStatus.PENDING: {ClinicStatus.ACTIVE, ClinicStatus.INACTIVE},
    ClinicStatus.ACTIVE: {ClinicStatus.SUSPENDED, ClinicStatus.INACTIVE},
    ClinicStatus.SUSPENDED: {ClinicStatus.ACTIVE, ClinicStatus.INACTIVE},
    ClinicStatus.INACTIVE: {ClinicStatus.PENDING},
}


class ClinicNotFoundError(Exception):
    """Raised when a vet clinic is not found."""

    def __init__(self, clinic_id: UUID) -> None:
        self.clinic_id = clinic_id
        self.message = f"Clinic {clinic_id} not found."
        super().__init__(self.message)


class InvalidStatusTransitionError(Exception):
    """Raised when a status transition is not allowed."""

    def __init__(self, current: str, requested: str) -> None:
        self.current = current
        self.requested = requested
        self.message = (
            f"Cannot transition from '{current}' to '{requested}'. "
            f"Allowed transitions: {', '.join(sorted(VALID_STATUS_TRANSITIONS.get(current, set())))}"
        )
        super().__init__(self.message)


async def create_clinic(
    db: AsyncSession, data: dict
) -> VetClinic:
    """Create a new partner vet clinic with 'pending' status."""
    clinic = VetClinic(**data)
    db.add(clinic)
    await db.flush()
    await db.refresh(clinic)
    logger.info("Created vet clinic %s (%s)", clinic.id, clinic.name)
    return clinic


async def get_clinic(db: AsyncSession, clinic_id: UUID) -> VetClinic:
    """Fetch a single clinic by ID. Raises ClinicNotFoundError if missing."""
    clinic = await db.get(VetClinic, clinic_id)
    if clinic is None:
        raise ClinicNotFoundError(clinic_id)
    return clinic


async def list_clinics(
    db: AsyncSession,
    *,
    status: str | None = None,
    city: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[VetClinic], int]:
    """List clinics with optional filters and pagination.

    Returns a tuple of (clinics, total_count).
    """
    query = select(VetClinic)
    count_query = select(func.count(VetClinic.id))

    if status:
        query = query.where(VetClinic.status == status)
        count_query = count_query.where(VetClinic.status == status)
    if city:
        query = query.where(VetClinic.city.ilike(f"%{city}%"))
        count_query = count_query.where(VetClinic.city.ilike(f"%{city}%"))

    query = query.order_by(VetClinic.name).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    clinics = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return clinics, total


async def update_clinic(
    db: AsyncSession, clinic_id: UUID, data: dict
) -> VetClinic:
    """Update clinic fields. Only non-None values in data are applied."""
    clinic = await get_clinic(db, clinic_id)

    for field, value in data.items():
        if value is not None:
            setattr(clinic, field, value)

    await db.flush()
    await db.refresh(clinic)
    logger.info("Updated vet clinic %s", clinic_id)
    return clinic


async def update_clinic_status(
    db: AsyncSession, clinic_id: UUID, new_status: str
) -> VetClinic:
    """Transition a clinic to a new status with validation.

    Sets partnership_start when transitioning to 'active'.
    Sets partnership_end when transitioning to 'inactive'.
    """
    clinic = await get_clinic(db, clinic_id)
    current = clinic.status

    allowed = VALID_STATUS_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise InvalidStatusTransitionError(current, new_status)

    clinic.status = new_status

    now = datetime.now(UTC)
    if new_status == ClinicStatus.ACTIVE and clinic.partnership_start is None:
        clinic.partnership_start = now
    elif new_status == ClinicStatus.INACTIVE:
        clinic.partnership_end = now

    await db.flush()
    await db.refresh(clinic)
    logger.info(
        "Clinic %s status: %s -> %s", clinic_id, current, new_status
    )
    return clinic


async def delete_clinic(db: AsyncSession, clinic_id: UUID) -> None:
    """Delete a clinic. Only allowed for clinics in 'pending' or 'inactive' status."""
    clinic = await get_clinic(db, clinic_id)

    if clinic.status not in (ClinicStatus.PENDING, ClinicStatus.INACTIVE):
        raise InvalidStatusTransitionError(
            clinic.status, "deleted"
        )

    await db.delete(clinic)
    await db.flush()
    logger.info("Deleted vet clinic %s", clinic_id)
