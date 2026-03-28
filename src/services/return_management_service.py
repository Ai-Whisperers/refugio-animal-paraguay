"""Service layer for adoption return/exchange management.

Handles creating return requests, processing returns (updating animal
and adoption status), and providing return analytics.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.return_request import (
    AnimalCondition,
    ReturnRequest,
    ReturnRequestStatus,
)

logger = logging.getLogger(__name__)

# Conditions that prevent the animal from going back to available
NON_AVAILABLE_CONDITIONS = {AnimalCondition.DECEASED.value, AnimalCondition.INJURED.value}

# Valid return request statuses
VALID_CONDITIONS = {c.value for c in AnimalCondition}


class ReturnManagementError(Exception):
    """Base error for return management operations."""


class AdoptionNotFoundError(ReturnManagementError):
    """Raised when the adoption request does not exist."""


class ReturnNotFoundError(ReturnManagementError):
    """Raised when a return request does not exist."""


class InvalidReturnError(ReturnManagementError):
    """Raised when a return request is not valid for the current adoption state."""


class DuplicateReturnError(ReturnManagementError):
    """Raised when a return request already exists for the adoption."""


async def create_return_request(
    db: AsyncSession,
    adoption_request_id: UUID,
    reason: str,
    animal_condition: str = AnimalCondition.HEALTHY.value,
    is_emergency: bool = False,
    requested_by: UUID | None = None,
) -> dict:
    """Create a new return request for an adoption.

    Validates that the adoption exists and is in an appropriate state.
    Checks for duplicate return requests.
    """
    from src.db.models.adoption_request import AdoptionRequest

    # Verify adoption exists
    result = await db.execute(
        select(AdoptionRequest).where(AdoptionRequest.id == adoption_request_id)
    )
    adoption = result.scalar_one_or_none()
    if adoption is None:
        raise AdoptionNotFoundError(f"Adoption request {adoption_request_id} not found")

    # Only approved adoptions can be returned
    if adoption.status not in ("approved", "completed"):
        raise InvalidReturnError(f"Cannot return adoption with status '{adoption.status}'")

    # Check for existing pending/approved return
    existing = await db.execute(
        select(func.count())
        .select_from(ReturnRequest)
        .where(
            ReturnRequest.adoption_request_id == adoption_request_id,
            ReturnRequest.status.in_(
                [
                    ReturnRequestStatus.PENDING.value,
                    ReturnRequestStatus.APPROVED.value,
                ]
            ),
        )
    )
    if existing.scalar_one() > 0:
        raise DuplicateReturnError(
            f"Active return request already exists for adoption {adoption_request_id}"
        )

    # Validate condition
    if animal_condition not in VALID_CONDITIONS:
        raise InvalidReturnError(f"Invalid animal condition: {animal_condition}")

    now = datetime.now(UTC)
    return_request = ReturnRequest(
        adoption_request_id=adoption_request_id,
        reason=reason,
        animal_condition=animal_condition,
        is_emergency=is_emergency,
        requested_by=requested_by,
        requested_at=now,
    )
    db.add(return_request)
    await db.flush()

    logger.info(
        "Return request created for adoption %s (emergency=%s, condition=%s)",
        adoption_request_id,
        is_emergency,
        animal_condition,
    )

    return {
        "id": return_request.id,
        "adoption_request_id": adoption_request_id,
        "reason": reason,
        "animal_condition": animal_condition,
        "is_emergency": is_emergency,
        "status": ReturnRequestStatus.PENDING.value,
        "requested_at": now,
    }


async def process_return(
    db: AsyncSession,
    return_request_id: UUID,
    staff_notes: str | None = None,
) -> dict:
    """Process an approved return: update adoption and animal status.

    Sets the return request to completed, adoption to 'returned',
    and animal back to 'available' (unless injured/deceased).
    """
    from src.db.models.adoption_request import AdoptionRequest
    from src.db.models.animal import Animal

    return_req = await db.get(ReturnRequest, return_request_id)
    if return_req is None:
        raise ReturnNotFoundError(f"Return request {return_request_id} not found")

    if return_req.status == ReturnRequestStatus.COMPLETED.value:
        raise InvalidReturnError("Return request already completed")

    now = datetime.now(UTC)

    # Update return request
    return_req.status = ReturnRequestStatus.COMPLETED.value
    return_req.staff_notes = staff_notes
    return_req.completed_at = now

    # Update adoption status
    adoption_result = await db.execute(
        select(AdoptionRequest).where(AdoptionRequest.id == return_req.adoption_request_id)
    )
    adoption = adoption_result.scalar_one_or_none()
    if adoption:
        adoption.status = "returned"

    # Update animal status (back to available unless injured/deceased)
    if adoption:
        animal_result = await db.execute(select(Animal).where(Animal.id == adoption.animal_id))
        animal = animal_result.scalar_one_or_none()
        if animal:
            if return_req.animal_condition not in NON_AVAILABLE_CONDITIONS:
                animal.status = "available"
            else:
                animal.status = "medical_hold"

    await db.flush()

    logger.info(
        "Return request %s processed (adoption %s -> returned)",
        return_request_id,
        return_req.adoption_request_id,
    )

    return {
        "id": return_req.id,
        "adoption_request_id": return_req.adoption_request_id,
        "status": ReturnRequestStatus.COMPLETED.value,
        "animal_condition": return_req.animal_condition,
        "staff_notes": staff_notes,
        "completed_at": now,
    }


async def get_return_request(
    db: AsyncSession,
    return_request_id: UUID,
) -> dict:
    """Fetch a single return request by ID."""
    return_req = await db.get(ReturnRequest, return_request_id)
    if return_req is None:
        raise ReturnNotFoundError(f"Return request {return_request_id} not found")

    return {
        "id": return_req.id,
        "adoption_request_id": return_req.adoption_request_id,
        "reason": return_req.reason,
        "animal_condition": return_req.animal_condition,
        "is_emergency": return_req.is_emergency,
        "status": return_req.status,
        "staff_notes": return_req.staff_notes,
        "requested_by": return_req.requested_by,
        "requested_at": return_req.requested_at,
        "completed_at": return_req.completed_at,
    }


async def list_return_requests(
    db: AsyncSession,
    status_filter: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """List return requests with optional status filter."""
    query = (
        select(ReturnRequest)
        .order_by(ReturnRequest.requested_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status_filter:
        query = query.where(ReturnRequest.status == status_filter)

    result = await db.execute(query)
    returns = result.scalars().all()

    return [
        {
            "id": r.id,
            "adoption_request_id": r.adoption_request_id,
            "reason": r.reason,
            "animal_condition": r.animal_condition,
            "is_emergency": r.is_emergency,
            "status": r.status,
            "requested_at": r.requested_at,
        }
        for r in returns
    ]


async def get_return_analytics(
    db: AsyncSession,
) -> dict:
    """Calculate return analytics: rate by condition, top reasons, emergency count."""
    # Total returns
    total_q = await db.execute(select(func.count()).select_from(ReturnRequest))
    total_returns = total_q.scalar_one()

    if total_returns == 0:
        return {
            "total_returns": 0,
            "by_condition": {},
            "emergency_count": 0,
            "emergency_pct": 0.0,
        }

    # By condition
    condition_q = await db.execute(
        select(
            ReturnRequest.animal_condition,
            func.count().label("count"),
        ).group_by(ReturnRequest.animal_condition)
    )
    by_condition = {row.animal_condition: row.count for row in condition_q}

    # Emergency count
    emergency_q = await db.execute(
        select(func.count()).select_from(ReturnRequest).where(ReturnRequest.is_emergency.is_(True))
    )
    emergency_count = emergency_q.scalar_one()
    emergency_pct = round(emergency_count / total_returns * 100, 1)

    return {
        "total_returns": total_returns,
        "by_condition": by_condition,
        "emergency_count": emergency_count,
        "emergency_pct": emergency_pct,
    }
