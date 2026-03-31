"""Home visit scheduling endpoints for adoption process.

Admin endpoints:
  POST  /api/admin/adoptions/{id}/home-visits   -- schedule visit
  GET   /api/admin/adoptions/{id}/home-visits   -- list visits for adoption
  PUT   /api/admin/home-visits/{id}             -- update visit details
  PATCH /api/admin/home-visits/{id}/complete    -- complete visit

Adopter endpoints:
  GET   /api/adoptions/{id}/home-visits         -- view scheduled visits
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.adoption_request import AdoptionRequest
from src.db.models.home_visit import HomeVisit
from src.db.models.user import User
from src.db.session import get_async_session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class HomeVisitCreateRequest(BaseModel):
    """Payload for scheduling a home visit."""

    scheduled_at: datetime
    address: str = Field(..., min_length=5, max_length=1000)
    staff_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=2000)


class HomeVisitUpdateRequest(BaseModel):
    """Payload for updating a home visit."""

    scheduled_at: datetime | None = None
    address: str | None = Field(default=None, min_length=5, max_length=1000)
    staff_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=2000)


class HomeVisitCompleteRequest(BaseModel):
    """Payload for completing a home visit."""

    notes: str | None = Field(default=None, max_length=5000)
    photos: list[str] = Field(default_factory=list, max_length=10)


class HomeVisitResponse(BaseModel):
    """Home visit response."""

    id: UUID
    adoption_request_id: UUID
    scheduled_at: str
    address: str
    staff_id: UUID | None
    status: str
    notes: str | None
    photos: list[str]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialise(visit: HomeVisit) -> dict:
    """Convert HomeVisit to response dict."""
    return {
        "id": visit.id,
        "adoption_request_id": visit.adoption_request_id,
        "scheduled_at": visit.scheduled_at.isoformat(),
        "address": visit.address,
        "staff_id": visit.staff_id,
        "status": visit.status,
        "notes": visit.notes,
        "photos": visit.photos or [],
        "created_at": visit.created_at.isoformat(),
        "updated_at": visit.updated_at.isoformat(),
    }


async def _get_visits_for_adoption(db: AsyncSession, adoption_id: UUID) -> list[HomeVisit]:
    """Get all non-deleted visits for an adoption, ordered by date."""
    stmt = (
        select(HomeVisit)
        .where(
            HomeVisit.adoption_request_id == adoption_id,
            HomeVisit.is_deleted.is_(False),
        )
        .order_by(HomeVisit.scheduled_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_visit_by_id(db: AsyncSession, visit_id: UUID) -> HomeVisit | None:
    """Get a single visit by ID."""
    visit = await db.get(HomeVisit, visit_id)
    if visit and not visit.is_deleted:
        return visit
    return None


# ---------------------------------------------------------------------------
# Admin Router
# ---------------------------------------------------------------------------

admin_router = APIRouter(
    prefix="/api/admin",
    tags=["admin-home-visits"],
    dependencies=[Depends(require_staff)],
)


@admin_router.post(
    "/adoptions/{adoption_id}/home-visits",
    response_model=HomeVisitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a home visit",
)
async def create_home_visit(
    adoption_id: UUID,
    payload: HomeVisitCreateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Schedule a new home visit for an adoption."""
    # Verify adoption exists
    adoption = await db.get(AdoptionRequest, adoption_id)
    if adoption is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Adoption request not found"},
        )

    # Verify staff exists if provided
    if payload.staff_id:
        staff = await db.get(User, payload.staff_id)
        if staff is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Staff member not found"},
            )

    # Validate scheduled_at is in the future
    if payload.scheduled_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Visit must be scheduled in the future"},
        )

    visit = HomeVisit(
        adoption_request_id=adoption_id,
        scheduled_at=payload.scheduled_at,
        address=payload.address,
        staff_id=payload.staff_id,
        notes=payload.notes,
        status="scheduled",
    )
    db.add(visit)
    await db.flush()
    await db.refresh(visit)

    logger.info(
        "Home visit scheduled for adoption %s on %s",
        adoption_id,
        payload.scheduled_at.isoformat(),
    )

    return _serialise(visit)


@admin_router.get(
    "/adoptions/{adoption_id}/home-visits",
    response_model=list[HomeVisitResponse],
    summary="List home visits for an adoption (admin)",
)
async def list_home_visits_admin(
    adoption_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    """Return all scheduled/completed visits for an adoption."""
    visits = await _get_visits_for_adoption(db, adoption_id)
    return [_serialise(v) for v in visits]


@admin_router.put(
    "/home-visits/{visit_id}",
    response_model=HomeVisitResponse,
    summary="Update home visit details",
)
async def update_home_visit(
    visit_id: UUID,
    payload: HomeVisitUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Update visit details (reschedule, change address, reassign staff)."""
    visit = await _get_visit_by_id(db, visit_id)
    if visit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Home visit not found"},
        )

    if visit.status != "scheduled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": f"Cannot update visit with status '{visit.status}'"},
        )

    if payload.scheduled_at is not None:
        visit.scheduled_at = payload.scheduled_at
    if payload.address is not None:
        visit.address = payload.address
    if payload.staff_id is not None:
        staff = await db.get(User, payload.staff_id)
        if staff is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Staff member not found"},
            )
        visit.staff_id = payload.staff_id
    if payload.notes is not None:
        visit.notes = payload.notes

    await db.flush()
    await db.refresh(visit)
    return _serialise(visit)


@admin_router.patch(
    "/home-visits/{visit_id}/complete",
    response_model=HomeVisitResponse,
    summary="Complete a home visit",
)
async def complete_home_visit(
    visit_id: UUID,
    payload: HomeVisitCompleteRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Mark a home visit as completed with notes and photos."""
    visit = await _get_visit_by_id(db, visit_id)
    if visit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Home visit not found"},
        )

    if visit.status != "scheduled":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": f"Cannot complete visit with status '{visit.status}'"},
        )

    visit.status = "completed"
    if payload.notes:
        existing = visit.notes or ""
        timestamp = datetime.now(UTC).isoformat()
        visit.notes = f"{existing}\n[{timestamp}] {payload.notes}".strip()
    if payload.photos:
        visit.photos = payload.photos

    await db.flush()
    await db.refresh(visit)

    logger.info("Home visit %s completed for adoption %s", visit_id, visit.adoption_request_id)

    return _serialise(visit)


# ---------------------------------------------------------------------------
# Adopter Router
# ---------------------------------------------------------------------------

public_router = APIRouter(
    prefix="/api/adoptions",
    tags=["home-visits"],
)


@public_router.get(
    "/{adoption_id}/home-visits",
    response_model=list[HomeVisitResponse],
    summary="View scheduled home visits (adopter)",
)
async def list_home_visits_public(
    adoption_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    """Return home visits for the adopter's adoption request."""
    visits = await _get_visits_for_adoption(db, adoption_id)
    return [_serialise(v) for v in visits]
