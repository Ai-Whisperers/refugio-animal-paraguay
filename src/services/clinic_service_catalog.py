"""Service layer for clinic service catalog management.

Handles CRUD for services offered by partner veterinary clinics,
including pricing in PYG and optional EUR equivalents.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.clinic_service import ClinicService
from src.db.models.vet_clinic import VetClinic

logger = logging.getLogger(__name__)


class ClinicServiceNotFoundError(Exception):
    """Raised when a clinic service is not found."""

    def __init__(self, service_id: UUID) -> None:
        self.service_id = service_id
        self.message = f"Clinic service {service_id} not found."
        super().__init__(self.message)


class ClinicNotFoundError(Exception):
    """Raised when the parent clinic does not exist."""

    def __init__(self, clinic_id: UUID) -> None:
        self.clinic_id = clinic_id
        self.message = f"Clinic {clinic_id} not found."
        super().__init__(self.message)


async def _verify_clinic_exists(db: AsyncSession, clinic_id: UUID) -> None:
    """Raise ClinicNotFoundError if the clinic does not exist."""
    clinic = await db.get(VetClinic, clinic_id)
    if clinic is None:
        raise ClinicNotFoundError(clinic_id)


async def create_service(db: AsyncSession, clinic_id: UUID, data: dict) -> ClinicService:
    """Create a new service in a clinic's catalog."""
    await _verify_clinic_exists(db, clinic_id)

    service = ClinicService(clinic_id=clinic_id, **data)
    db.add(service)
    await db.flush()
    await db.refresh(service)
    logger.info(
        "Created clinic service %s for clinic %s (%s)",
        service.id,
        clinic_id,
        service.name,
    )
    return service


async def get_service(db: AsyncSession, clinic_id: UUID, service_id: UUID) -> ClinicService:
    """Fetch a single service by ID, scoped to a clinic."""
    await _verify_clinic_exists(db, clinic_id)

    result = await db.execute(
        select(ClinicService).where(
            ClinicService.id == service_id,
            ClinicService.clinic_id == clinic_id,
        )
    )
    service = result.scalar_one_or_none()
    if service is None:
        raise ClinicServiceNotFoundError(service_id)
    return service


async def list_services(
    db: AsyncSession,
    clinic_id: UUID,
    *,
    category: str | None = None,
    active_only: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ClinicService], int]:
    """List services for a clinic with optional filters and pagination.

    Returns (services, total_count).
    """
    await _verify_clinic_exists(db, clinic_id)

    query = select(ClinicService).where(ClinicService.clinic_id == clinic_id)
    count_query = select(func.count(ClinicService.id)).where(ClinicService.clinic_id == clinic_id)

    if category:
        query = query.where(ClinicService.category == category)
        count_query = count_query.where(ClinicService.category == category)
    if active_only:
        query = query.where(ClinicService.is_active.is_(True))
        count_query = count_query.where(ClinicService.is_active.is_(True))

    query = (
        query.order_by(ClinicService.category, ClinicService.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    services = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return services, total


async def update_service(
    db: AsyncSession, clinic_id: UUID, service_id: UUID, data: dict
) -> ClinicService:
    """Update service fields. Only non-None values in data are applied."""
    service = await get_service(db, clinic_id, service_id)

    for field, value in data.items():
        if value is not None:
            setattr(service, field, value)

    await db.flush()
    await db.refresh(service)
    logger.info("Updated clinic service %s", service_id)
    return service


async def delete_service(db: AsyncSession, clinic_id: UUID, service_id: UUID) -> None:
    """Delete a service from the catalog."""
    service = await get_service(db, clinic_id, service_id)
    await db.delete(service)
    await db.flush()
    logger.info("Deleted clinic service %s from clinic %s", service_id, clinic_id)
