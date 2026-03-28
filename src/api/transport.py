"""API endpoints for animal transport request management.

Provides endpoints for creating, viewing, updating, and cancelling
transport requests for animals.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user
from src.db.models.user import User
from src.db.session import get_db
from src.services.transport_service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    InvalidStatusTransitionError,
    InvalidTransportError,
    TransportNotFoundError,
    cancel_transport_request,
    create_transport_request,
    get_transport_request,
    list_transport_requests,
    update_transport_request,
)

router = APIRouter(tags=["Transport"])


# --- Schemas ---


class CreateTransportRequest(BaseModel):
    """Request body for creating a transport request."""

    pickup_location: str
    destination: str
    urgency: str = "normal"
    animal_id: UUID | None = None
    preferred_date: datetime | None = None
    notes: str | None = None


class UpdateTransportRequest(BaseModel):
    """Request body for updating a transport request."""

    pickup_location: str | None = None
    destination: str | None = None
    urgency: str | None = None
    animal_id: UUID | None = None
    preferred_date: datetime | None = None
    notes: str | None = None
    status: str | None = None
    claimed_by: UUID | None = None


class TransportRequestResponse(BaseModel):
    """Transport request details."""

    id: UUID
    requester_id: UUID
    animal_id: UUID | None = None
    pickup_location: str
    destination: str
    urgency: str
    preferred_date: datetime | None = None
    status: str
    notes: str | None = None
    claimed_by: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransportListResponse(BaseModel):
    """Paginated list of transport requests."""

    requests: list[TransportRequestResponse]
    total: int
    limit: int
    offset: int


# --- Endpoints ---


@router.post(
    "/api/transport",
    response_model=TransportRequestResponse,
    status_code=201,
)
async def create_transport(
    body: CreateTransportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> dict:
    """Create a new transport request."""
    try:
        return await create_transport_request(
            db=db,
            requester_id=current_user.id,
            pickup_location=body.pickup_location,
            destination=body.destination,
            urgency=body.urgency,
            animal_id=body.animal_id,
            preferred_date=body.preferred_date,
            notes=body.notes,
        )
    except InvalidTransportError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.get(
    "/api/transport/{request_id}",
    response_model=TransportRequestResponse,
)
async def get_transport(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(_get_current_user),
) -> dict:
    """Get a transport request by ID."""
    try:
        return await get_transport_request(db=db, request_id=request_id)
    except TransportNotFoundError:
        raise HTTPException(status_code=404, detail="Transport request not found") from None


@router.put(
    "/api/transport/{request_id}",
    response_model=TransportRequestResponse,
)
async def update_transport(
    request_id: UUID,
    body: UpdateTransportRequest,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(_get_current_user),
) -> dict:
    """Update a transport request."""
    try:
        return await update_transport_request(
            db=db,
            request_id=request_id,
            pickup_location=body.pickup_location,
            destination=body.destination,
            urgency=body.urgency,
            animal_id=body.animal_id,
            preferred_date=body.preferred_date,
            notes=body.notes,
            status=body.status,
            claimed_by=body.claimed_by,
        )
    except TransportNotFoundError:
        raise HTTPException(status_code=404, detail="Transport request not found") from None
    except (InvalidTransportError, InvalidStatusTransitionError) as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.delete(
    "/api/transport/{request_id}",
    response_model=TransportRequestResponse,
)
async def cancel_transport(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> dict:
    """Cancel a transport request."""
    try:
        return await cancel_transport_request(db=db, request_id=request_id, user_id=current_user.id)
    except TransportNotFoundError:
        raise HTTPException(status_code=404, detail="Transport request not found") from None
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None


@router.get(
    "/api/transport",
    response_model=TransportListResponse,
)
async def list_transports(
    status: str | None = Query(default=None, description="Filter by status"),
    urgency: str | None = Query(default=None, description="Filter by urgency"),
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(_get_current_user),
) -> dict:
    """List transport requests with optional filters."""
    return await list_transport_requests(
        db=db,
        status_filter=status,
        urgency_filter=urgency,
        limit=limit,
        offset=offset,
    )
