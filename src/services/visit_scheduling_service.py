"""Service layer for adopter portal visit scheduling.

Handles:
  - Creating visit requests with proposed time slots
  - Listing all visits and pending requests for an adopter
  - Cancelling pending visit requests
  - Resolving an adopter's profile from their user account
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest
from src.db.models.home_visit import HomeVisit
from src.db.models.visit_request import VisitRequest, VisitRequestStatus

logger = logging.getLogger(__name__)


class VisitSchedulingError(Exception):
    """Raised when a visit scheduling action is invalid."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class VisitSummary:
    """Unified view of a scheduled home visit for the adopter portal."""

    id: UUID
    adoption_request_id: UUID
    scheduled_at: datetime
    address: str
    status: str
    notes: str | None


@dataclass(frozen=True)
class VisitRequestSummary:
    """Summary of an adopter-submitted visit request."""

    id: UUID
    adoption_request_id: UUID
    proposed_slots: list[str]
    address: str
    notes: str | None
    status: str
    created_at: datetime


async def get_adopter_by_email(email: str, db: AsyncSession) -> Adopter | None:
    """Fetch an active adopter record by email address."""
    stmt = select(Adopter).where(
        Adopter.email == email,
        Adopter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def validate_adoption_request_belongs_to_adopter(
    adoption_request_id: UUID,
    adopter_id: UUID,
    db: AsyncSession,
) -> AdoptionRequest:
    """Verify the adoption request exists and belongs to the adopter.

    Raises VisitSchedulingError if not found or not owned.
    """
    stmt = select(AdoptionRequest).where(
        AdoptionRequest.id == adoption_request_id,
        AdoptionRequest.adopter_id == adopter_id,
    )
    result = await db.execute(stmt)
    adoption = result.scalar_one_or_none()
    if adoption is None:
        raise VisitSchedulingError(
            "Adoption request not found or does not belong to you.",
            status_code=404,
        )
    return adoption


async def create_visit_request(
    adoption_request_id: UUID,
    adopter_id: UUID,
    proposed_slots: list[str],
    address: str,
    notes: str | None,
    db: AsyncSession,
) -> VisitRequest:
    """Create a new visit request with the adopter's proposed availability.

    Validates that:
    - The adoption request belongs to this adopter
    - At least one proposed slot is provided
    - No more than 5 slots are proposed
    """
    if not proposed_slots:
        raise VisitSchedulingError("At least one proposed time slot is required.")
    if len(proposed_slots) > 5:
        raise VisitSchedulingError("A maximum of 5 proposed time slots are allowed.")

    await validate_adoption_request_belongs_to_adopter(adoption_request_id, adopter_id, db)

    visit_request = VisitRequest(
        adoption_request_id=adoption_request_id,
        adopter_id=adopter_id,
        proposed_slots=proposed_slots,
        address=address,
        notes=notes,
        status=VisitRequestStatus.PENDING,
    )
    db.add(visit_request)
    await db.flush()
    await db.refresh(visit_request)

    logger.info(
        "Visit request created",
        extra={
            "adoption_request_id": str(adoption_request_id),
            "adopter_id": str(adopter_id),
            "slots": len(proposed_slots),
        },
    )

    return visit_request


async def list_adopter_visits(
    adopter_id: UUID,
    db: AsyncSession,
) -> tuple[list[VisitSummary], list[VisitRequestSummary]]:
    """Return all scheduled visits and pending visit requests for an adopter.

    Returns two lists:
      - confirmed_visits: HomeVisit records linked to the adopter's adoptions
      - pending_requests: VisitRequest records with status 'pending'
    """
    # Get all adoption request IDs for this adopter
    adoption_stmt = select(AdoptionRequest.id).where(AdoptionRequest.adopter_id == adopter_id)
    adoption_result = await db.execute(adoption_stmt)
    adoption_ids = [row[0] for row in adoption_result.fetchall()]

    if not adoption_ids:
        return [], []

    # Fetch scheduled home visits
    visit_stmt = (
        select(HomeVisit)
        .where(
            HomeVisit.adoption_request_id.in_(adoption_ids),
            HomeVisit.is_deleted.is_(False),
        )
        .order_by(HomeVisit.scheduled_at.asc())
    )
    visit_result = await db.execute(visit_stmt)
    visits = [
        VisitSummary(
            id=v.id,
            adoption_request_id=v.adoption_request_id,
            scheduled_at=v.scheduled_at,
            address=v.address,
            status=v.status,
            notes=v.notes,
        )
        for v in visit_result.scalars().all()
    ]

    # Fetch pending visit requests
    req_stmt = (
        select(VisitRequest)
        .where(
            VisitRequest.adopter_id == adopter_id,
            VisitRequest.status == VisitRequestStatus.PENDING,
        )
        .order_by(VisitRequest.created_at.desc())
    )
    req_result = await db.execute(req_stmt)
    requests = [
        VisitRequestSummary(
            id=r.id,
            adoption_request_id=r.adoption_request_id,
            proposed_slots=r.proposed_slots,
            address=r.address,
            notes=r.notes,
            status=r.status,
            created_at=r.created_at,
        )
        for r in req_result.scalars().all()
    ]

    return visits, requests


async def cancel_visit_request(
    request_id: UUID,
    adopter_id: UUID,
    db: AsyncSession,
) -> None:
    """Cancel a pending visit request.

    Raises VisitSchedulingError if:
    - Request not found
    - Request does not belong to this adopter
    - Request is not in 'pending' status
    """
    visit_request = await db.get(VisitRequest, request_id)
    if visit_request is None:
        raise VisitSchedulingError("Visit request not found.", status_code=404)
    if visit_request.adopter_id != adopter_id:
        raise VisitSchedulingError(
            "You do not have permission to cancel this visit request.",
            status_code=403,
        )
    if visit_request.status != VisitRequestStatus.PENDING:
        raise VisitSchedulingError(
            f"Cannot cancel a visit request with status '{visit_request.status}'.",
            status_code=409,
        )

    visit_request.status = VisitRequestStatus.CANCELLED
    visit_request.updated_at = datetime.now(UTC)
    await db.flush()

    logger.info(
        "Visit request cancelled by adopter",
        extra={
            "request_id": str(request_id),
            "adopter_id": str(adopter_id),
        },
    )
