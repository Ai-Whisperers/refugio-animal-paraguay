"""API endpoints for vet-transport integration.

Links transport requests to vet visits for coordinated animal logistics.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.vet_transport_service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    DuplicateLinkError,
    InvalidLinkError,
    InvalidStatusTransitionError,
    LinkNotFoundError,
    create_link,
    delete_link,
    get_link,
    list_links,
    update_link_status,
)

router = APIRouter(tags=["Vet Transport Integration"])


# --- Schemas ---


class CreateLinkRequest(BaseModel):
    """Request body for creating a vet-transport link."""

    transport_request_id: UUID
    vet_visit_id: UUID
    animal_id: UUID
    pickup_time: datetime | None = None
    dropoff_time: datetime | None = None
    notes: str | None = None


class UpdateLinkStatusRequest(BaseModel):
    """Request body for updating link status."""

    status: str


class LinkResponse(BaseModel):
    """Vet-transport link details."""

    id: UUID
    transport_request_id: UUID
    vet_visit_id: UUID
    animal_id: UUID
    status: str
    pickup_time: datetime | None = None
    dropoff_time: datetime | None = None
    notes: str | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LinkListResponse(BaseModel):
    """Paginated list of vet-transport links."""

    links: list[LinkResponse]
    total: int
    limit: int
    offset: int


# --- Endpoints ---


@router.post(
    "/api/vet-transport/links",
    response_model=LinkResponse,
    status_code=201,
)
async def create_link_endpoint(
    body: CreateLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> dict:
    """Create a link between a transport request and a vet visit."""
    try:
        return await create_link(
            db=db,
            transport_request_id=body.transport_request_id,
            vet_visit_id=body.vet_visit_id,
            animal_id=body.animal_id,
            created_by=current_user.id,
            pickup_time=body.pickup_time,
            dropoff_time=body.dropoff_time,
            notes=body.notes,
        )
    except DuplicateLinkError as e:
        raise HTTPException(status_code=409, detail=str(e)) from None
    except InvalidLinkError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.get(
    "/api/vet-transport/links",
    response_model=LinkListResponse,
)
async def list_links_endpoint(
    transport_request_id: UUID | None = Query(default=None),
    vet_visit_id: UUID | None = Query(default=None),
    animal_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(_get_current_user),
) -> dict:
    """List vet-transport links with optional filters."""
    return await list_links(
        db=db,
        transport_request_id=transport_request_id,
        vet_visit_id=vet_visit_id,
        animal_id=animal_id,
        status_filter=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/api/vet-transport/links/{link_id}",
    response_model=LinkResponse,
)
async def get_link_endpoint(
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(_get_current_user),
) -> dict:
    """Get a vet-transport link by ID."""
    try:
        return await get_link(db=db, link_id=link_id)
    except LinkNotFoundError:
        raise HTTPException(status_code=404, detail="Link not found") from None


@router.put(
    "/api/vet-transport/links/{link_id}/status",
    response_model=LinkResponse,
)
async def update_link_status_endpoint(
    link_id: UUID,
    body: UpdateLinkStatusRequest,
    db: AsyncSession = Depends(get_db),
    _staff: User = Depends(require_staff),
) -> dict:
    """Update the status of a vet-transport link."""
    try:
        return await update_link_status(
            db=db,
            link_id=link_id,
            new_status=body.status,
        )
    except LinkNotFoundError:
        raise HTTPException(status_code=404, detail="Link not found") from None
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e)) from None
    except InvalidLinkError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.delete(
    "/api/vet-transport/links/{link_id}",
    status_code=204,
)
async def delete_link_endpoint(
    link_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: User = Depends(require_staff),
) -> None:
    """Delete a scheduled vet-transport link."""
    try:
        await delete_link(db=db, link_id=link_id)
    except LinkNotFoundError:
        raise HTTPException(status_code=404, detail="Link not found") from None
    except InvalidLinkError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None
