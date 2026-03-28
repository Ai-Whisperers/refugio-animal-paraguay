"""Service layer for vet-transport integration.

Links transport requests to vet visits for coordinated animal logistics.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.vet_transport_link import (
    VALID_LINK_STATUSES,
    LinkStatus,
    VetTransportLink,
)

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

VALID_TRANSITIONS: dict[str, set[str]] = {
    "scheduled": {"in_progress", "cancelled"},
    "in_progress": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


class VetTransportError(Exception):
    """Base error for vet-transport operations."""


class LinkNotFoundError(VetTransportError):
    """Raised when a link does not exist."""


class DuplicateLinkError(VetTransportError):
    """Raised when a transport-visit link already exists."""


class InvalidLinkError(VetTransportError):
    """Raised when link validation fails."""


class InvalidStatusTransitionError(VetTransportError):
    """Raised when a status transition is not allowed."""


async def create_link(
    db: AsyncSession,
    transport_request_id: UUID,
    vet_visit_id: UUID,
    animal_id: UUID,
    created_by: UUID,
    pickup_time: datetime | None = None,
    dropoff_time: datetime | None = None,
    notes: str | None = None,
) -> dict:
    """Create a link between a transport request and a vet visit."""
    # Check for duplicate
    existing = await db.execute(
        select(func.count())
        .select_from(VetTransportLink)
        .where(
            VetTransportLink.transport_request_id == transport_request_id,
            VetTransportLink.vet_visit_id == vet_visit_id,
        )
    )
    if existing.scalar_one() > 0:
        raise DuplicateLinkError(
            f"Link between transport {transport_request_id} and visit {vet_visit_id} already exists"
        )

    if pickup_time and dropoff_time and dropoff_time <= pickup_time:
        raise InvalidLinkError("Dropoff time must be after pickup time")

    link = VetTransportLink(
        transport_request_id=transport_request_id,
        vet_visit_id=vet_visit_id,
        animal_id=animal_id,
        created_by=created_by,
        status=LinkStatus.SCHEDULED.value,
        pickup_time=pickup_time,
        dropoff_time=dropoff_time,
        notes=notes,
    )
    db.add(link)
    await db.flush()
    await db.refresh(link)

    return _link_to_dict(link)


async def get_link(db: AsyncSession, link_id: UUID) -> dict:
    """Get a vet-transport link by ID."""
    result = await db.execute(select(VetTransportLink).where(VetTransportLink.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise LinkNotFoundError(f"Link {link_id} not found")
    return _link_to_dict(link)


async def list_links(
    db: AsyncSession,
    transport_request_id: UUID | None = None,
    vet_visit_id: UUID | None = None,
    animal_id: UUID | None = None,
    status_filter: str | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> dict:
    """List vet-transport links with optional filters."""
    base_query = select(VetTransportLink)

    if transport_request_id is not None:
        base_query = base_query.where(VetTransportLink.transport_request_id == transport_request_id)
    if vet_visit_id is not None:
        base_query = base_query.where(VetTransportLink.vet_visit_id == vet_visit_id)
    if animal_id is not None:
        base_query = base_query.where(VetTransportLink.animal_id == animal_id)
    if status_filter is not None:
        base_query = base_query.where(VetTransportLink.status == status_filter)

    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    result = await db.execute(
        base_query.order_by(VetTransportLink.created_at.desc()).limit(limit).offset(offset)
    )
    links = list(result.scalars().all())

    return {
        "links": [_link_to_dict(link) for link in links],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def update_link_status(
    db: AsyncSession,
    link_id: UUID,
    new_status: str,
) -> dict:
    """Update the status of a vet-transport link."""
    result = await db.execute(select(VetTransportLink).where(VetTransportLink.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise LinkNotFoundError(f"Link {link_id} not found")

    if new_status not in VALID_LINK_STATUSES:
        raise InvalidLinkError(f"Invalid status '{new_status}'")

    current = link.status
    allowed = VALID_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise InvalidStatusTransitionError(f"Cannot transition from '{current}' to '{new_status}'")

    link.status = new_status
    await db.flush()
    await db.refresh(link)

    return _link_to_dict(link)


async def delete_link(db: AsyncSession, link_id: UUID) -> None:
    """Delete a vet-transport link (only if scheduled)."""
    result = await db.execute(select(VetTransportLink).where(VetTransportLink.id == link_id))
    link = result.scalar_one_or_none()
    if link is None:
        raise LinkNotFoundError(f"Link {link_id} not found")

    if link.status != LinkStatus.SCHEDULED:
        raise InvalidLinkError(f"Cannot delete link with status '{link.status}'")

    await db.delete(link)
    await db.flush()


def _link_to_dict(link: VetTransportLink) -> dict:
    """Convert a VetTransportLink to a dict."""
    return {
        "id": link.id,
        "transport_request_id": link.transport_request_id,
        "vet_visit_id": link.vet_visit_id,
        "animal_id": link.animal_id,
        "status": link.status,
        "pickup_time": link.pickup_time,
        "dropoff_time": link.dropoff_time,
        "notes": link.notes,
        "created_by": link.created_by,
        "created_at": link.created_at,
        "updated_at": link.updated_at,
    }
