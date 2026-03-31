"""Portal visit scheduling endpoints for authenticated adopters.

Endpoints:
  GET    /portal/visits                            -- list scheduled visits + pending requests
  POST   /portal/visit-requests                    -- adopter requests a home visit
  DELETE /portal/visit-requests/{request_id}       -- adopter cancels a pending request
  GET    /admin/visit-requests                     -- staff views all pending visit requests
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import COMMON_RESPONSES
from src.services.visit_scheduling_service import (
    VisitRequestSummary,
    VisitSchedulingError,
    VisitSummary,
    cancel_visit_request,
    create_visit_request,
    get_adopter_by_email,
    list_adopter_visits,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["portal-visits"], responses=COMMON_RESPONSES)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class VisitSummaryResponse(BaseModel):
    """A scheduled home visit visible to an adopter."""

    id: UUID
    adoption_request_id: UUID
    scheduled_at: datetime
    address: str
    status: str
    notes: str | None


class VisitRequestResponse(BaseModel):
    """An adopter-submitted visit request awaiting staff confirmation."""

    id: UUID
    adoption_request_id: UUID
    proposed_slots: list[str]
    address: str
    notes: str | None
    status: str
    created_at: datetime


class AdopterVisitDashboardResponse(BaseModel):
    """Combined view of scheduled visits and pending requests for the adopter."""

    scheduled_visits: list[VisitSummaryResponse]
    pending_requests: list[VisitRequestResponse]
    total_scheduled: int
    total_pending: int


class CreateVisitRequestPayload(BaseModel):
    """Payload to submit a visit scheduling request."""

    adoption_request_id: UUID = Field(..., description="The adoption application to schedule for")
    proposed_slots: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="ISO 8601 datetime strings for preferred visit times (1-5 slots)",
    )
    address: str = Field(..., min_length=5, max_length=1000, description="Visit address")
    notes: str | None = Field(default=None, max_length=2000, description="Additional notes")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _resolve_adopter(user: User, db: AsyncSession) -> UUID:
    """Resolve adopter ID for the authenticated user; raise 404 if not found."""
    adopter = await get_adopter_by_email(user.email, db)
    if adopter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No adopter profile found for this user.",
        )
    return adopter.id


def _format_visit(v: VisitSummary) -> VisitSummaryResponse:
    return VisitSummaryResponse(
        id=v.id,
        adoption_request_id=v.adoption_request_id,
        scheduled_at=v.scheduled_at,
        address=v.address,
        status=v.status,
        notes=v.notes,
    )


def _format_request(r: VisitRequestSummary) -> VisitRequestResponse:
    return VisitRequestResponse(
        id=r.id,
        adoption_request_id=r.adoption_request_id,
        proposed_slots=r.proposed_slots,
        address=r.address,
        notes=r.notes,
        status=r.status,
        created_at=r.created_at,
    )


# ---------------------------------------------------------------------------
# Adopter endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/portal/visits",
    response_model=AdopterVisitDashboardResponse,
    summary="View my visits and visit requests",
    description=(
        "Returns all scheduled home visits and pending visit requests "
        "for the authenticated adopter."
    ),
)
async def get_my_visits(
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdopterVisitDashboardResponse:
    """Return the adopter's visit dashboard — scheduled visits plus open requests."""
    adopter_id = await _resolve_adopter(user, db)
    visits, requests = await list_adopter_visits(adopter_id, db)
    return AdopterVisitDashboardResponse(
        scheduled_visits=[_format_visit(v) for v in visits],
        pending_requests=[_format_request(r) for r in requests],
        total_scheduled=len(visits),
        total_pending=len(requests),
    )


@router.post(
    "/portal/visit-requests",
    response_model=VisitRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a home visit",
    description=(
        "Adopter submits preferred visit time slots for a home visit. "
        "Staff will confirm one slot and schedule the visit."
    ),
    responses={
        404: {"description": "Adoption request not found"},
        409: {"description": "Conflict with visit request state"},
    },
)
async def request_visit(
    payload: CreateVisitRequestPayload,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VisitRequestResponse:
    """Submit a visit scheduling request for an adoption."""
    adopter_id = await _resolve_adopter(user, db)
    try:
        visit_request = await create_visit_request(
            adoption_request_id=payload.adoption_request_id,
            adopter_id=adopter_id,
            proposed_slots=payload.proposed_slots,
            address=payload.address,
            notes=payload.notes,
            db=db,
        )
    except VisitSchedulingError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

    return VisitRequestResponse(
        id=visit_request.id,
        adoption_request_id=visit_request.adoption_request_id,
        proposed_slots=visit_request.proposed_slots,
        address=visit_request.address,
        notes=visit_request.notes,
        status=visit_request.status,
        created_at=visit_request.created_at,
    )


@router.delete(
    "/portal/visit-requests/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a visit request",
    description="Adopter cancels a pending visit scheduling request.",
    responses={
        403: {"description": "Not your visit request"},
        404: {"description": "Visit request not found"},
        409: {"description": "Request is not pending"},
    },
)
async def cancel_my_visit_request(
    request_id: UUID,
    user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Cancel a pending visit request."""
    adopter_id = await _resolve_adopter(user, db)
    try:
        await cancel_visit_request(request_id, adopter_id, db)
    except VisitSchedulingError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc


# ---------------------------------------------------------------------------
# Staff endpoint — view all pending visit requests
# ---------------------------------------------------------------------------


@router.get(
    "/admin/visit-requests",
    response_model=list[VisitRequestResponse],
    summary="List all pending visit requests (staff)",
    description="Staff can view all adopter-submitted visit requests awaiting confirmation.",
)
async def list_pending_visit_requests_staff(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[VisitRequestResponse]:
    """Return all pending visit requests for staff review."""
    from sqlalchemy import select

    from src.db.models.visit_request import VisitRequest, VisitRequestStatus

    stmt = (
        select(VisitRequest)
        .where(VisitRequest.status == VisitRequestStatus.PENDING)
        .order_by(VisitRequest.created_at.asc())
    )
    result = await db.execute(stmt)
    requests = result.scalars().all()
    return [
        VisitRequestResponse(
            id=r.id,
            adoption_request_id=r.adoption_request_id,
            proposed_slots=r.proposed_slots,
            address=r.address,
            notes=r.notes,
            status=r.status,
            created_at=r.created_at,
        )
        for r in requests
    ]
