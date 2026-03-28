"""Service layer for animal transport request management.

Handles CRUD operations for transport requests with validation,
status transitions, and filtering.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.transport_request import (
    VALID_STATUSES,
    VALID_URGENCIES,
    TransportRequest,
    TransportStatus,
    TransportUrgency,
)

logger = logging.getLogger(__name__)

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Valid status transitions
VALID_TRANSITIONS: dict[str, set[str]] = {
    TransportStatus.OPEN: {TransportStatus.CLAIMED, TransportStatus.CANCELLED},
    TransportStatus.CLAIMED: {
        TransportStatus.IN_TRANSIT,
        TransportStatus.OPEN,
        TransportStatus.CANCELLED,
    },
    TransportStatus.IN_TRANSIT: {TransportStatus.DELIVERED, TransportStatus.CANCELLED},
    TransportStatus.DELIVERED: set(),
    TransportStatus.CANCELLED: set(),
}


class TransportError(Exception):
    """Base error for transport operations."""


class TransportNotFoundError(TransportError):
    """Raised when a transport request does not exist."""


class InvalidTransportError(TransportError):
    """Raised when validation fails for a transport request."""


class InvalidStatusTransitionError(TransportError):
    """Raised when a status transition is not allowed."""


async def create_transport_request(
    db: AsyncSession,
    requester_id: UUID,
    pickup_location: str,
    destination: str,
    urgency: str = TransportUrgency.NORMAL.value,
    animal_id: UUID | None = None,
    preferred_date: datetime | None = None,
    notes: str | None = None,
) -> dict:
    """Create a new transport request."""
    if urgency not in VALID_URGENCIES:
        raise InvalidTransportError(
            f"Invalid urgency '{urgency}', must be one of {VALID_URGENCIES}"
        )

    if not pickup_location.strip():
        raise InvalidTransportError("Pickup location is required")
    if not destination.strip():
        raise InvalidTransportError("Destination is required")

    request = TransportRequest(
        requester_id=requester_id,
        animal_id=animal_id,
        pickup_location=pickup_location.strip(),
        destination=destination.strip(),
        urgency=urgency,
        preferred_date=preferred_date,
        notes=notes,
        status=TransportStatus.OPEN.value,
    )
    db.add(request)
    await db.flush()
    await db.refresh(request)

    return _request_to_dict(request)


async def get_transport_request(db: AsyncSession, request_id: UUID) -> dict:
    """Get a transport request by ID."""
    result = await db.execute(select(TransportRequest).where(TransportRequest.id == request_id))
    request = result.scalar_one_or_none()
    if request is None:
        raise TransportNotFoundError(f"Transport request {request_id} not found")
    return _request_to_dict(request)


async def update_transport_request(
    db: AsyncSession,
    request_id: UUID,
    pickup_location: str | None = None,
    destination: str | None = None,
    urgency: str | None = None,
    animal_id: UUID | None = None,
    preferred_date: datetime | None = None,
    notes: str | None = None,
    status: str | None = None,
    claimed_by: UUID | None = None,
) -> dict:
    """Update a transport request."""
    result = await db.execute(select(TransportRequest).where(TransportRequest.id == request_id))
    request = result.scalar_one_or_none()
    if request is None:
        raise TransportNotFoundError(f"Transport request {request_id} not found")

    if status is not None and status != request.status:
        if status not in VALID_STATUSES:
            raise InvalidTransportError(f"Invalid status '{status}'")
        allowed = VALID_TRANSITIONS.get(request.status, set())
        if status not in allowed:
            raise InvalidStatusTransitionError(
                f"Cannot transition from '{request.status}' to '{status}'"
            )
        request.status = status

    if urgency is not None:
        if urgency not in VALID_URGENCIES:
            raise InvalidTransportError(f"Invalid urgency '{urgency}'")
        request.urgency = urgency

    if pickup_location is not None:
        if not pickup_location.strip():
            raise InvalidTransportError("Pickup location cannot be empty")
        request.pickup_location = pickup_location.strip()

    if destination is not None:
        if not destination.strip():
            raise InvalidTransportError("Destination cannot be empty")
        request.destination = destination.strip()

    if animal_id is not None:
        request.animal_id = animal_id
    if preferred_date is not None:
        request.preferred_date = preferred_date
    if notes is not None:
        request.notes = notes
    if claimed_by is not None:
        request.claimed_by = claimed_by

    await db.flush()
    await db.refresh(request)

    return _request_to_dict(request)


async def cancel_transport_request(
    db: AsyncSession,
    request_id: UUID,
    user_id: UUID,
) -> dict:
    """Cancel a transport request.

    Only the requester or staff can cancel. Terminal states cannot be cancelled.
    """
    result = await db.execute(select(TransportRequest).where(TransportRequest.id == request_id))
    request = result.scalar_one_or_none()
    if request is None:
        raise TransportNotFoundError(f"Transport request {request_id} not found")

    if request.status in (TransportStatus.DELIVERED, TransportStatus.CANCELLED):
        raise InvalidStatusTransitionError(
            f"Cannot cancel a request that is already '{request.status}'"
        )

    request.status = TransportStatus.CANCELLED.value
    await db.flush()
    await db.refresh(request)

    return _request_to_dict(request)


async def list_transport_requests(
    db: AsyncSession,
    status_filter: str | None = None,
    urgency_filter: str | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> dict:
    """List transport requests with optional filters."""
    base_query = select(TransportRequest)

    if status_filter is not None:
        base_query = base_query.where(TransportRequest.status == status_filter)
    if urgency_filter is not None:
        base_query = base_query.where(TransportRequest.urgency == urgency_filter)

    # Count
    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Fetch
    result = await db.execute(
        base_query.order_by(TransportRequest.created_at.desc()).limit(limit).offset(offset)
    )
    requests = list(result.scalars().all())

    return {
        "requests": [_request_to_dict(r) for r in requests],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def _request_to_dict(request: TransportRequest) -> dict:
    """Convert a TransportRequest model to a dict."""
    return {
        "id": request.id,
        "requester_id": request.requester_id,
        "animal_id": request.animal_id,
        "pickup_location": request.pickup_location,
        "destination": request.destination,
        "urgency": request.urgency,
        "preferred_date": request.preferred_date,
        "status": request.status,
        "notes": request.notes,
        "claimed_by": request.claimed_by,
        "created_at": request.created_at,
        "updated_at": request.updated_at,
    }
