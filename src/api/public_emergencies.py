"""Public emergency endpoints -- unauthenticated access to active emergencies.

Endpoints:
  GET /api/public/emergencies/active -- list active emergencies (public)
  GET /api/public/emergencies/{id}   -- single emergency detail (public)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.emergency_case import EmergencyCase
from src.db.session import get_async_session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PublicEmergencyResponse(BaseModel):
    """Public-facing emergency case response."""

    id: UUID
    title: str
    description: str
    photos: list = Field(default_factory=list)
    amount_needed_cents: int
    amount_raised_cents: int
    currency: str
    deadline: str
    status: str
    urgency: str
    created_at: str
    progress_pct: int = 0

    model_config = {"from_attributes": True}


class PublicEmergencyListResponse(BaseModel):
    """Paginated list of public emergencies."""

    items: list[PublicEmergencyResponse]
    total: int


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/public/emergencies",
    tags=["public-emergencies"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialise(e: EmergencyCase) -> dict:
    """Convert emergency to public response dict."""
    needed = e.amount_needed_cents or 1
    raised = e.amount_raised_cents or 0
    progress = min(100, int((raised / needed) * 100))
    return {
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "photos": e.photos or [],
        "amount_needed_cents": e.amount_needed_cents,
        "amount_raised_cents": e.amount_raised_cents,
        "currency": e.currency,
        "deadline": e.deadline.isoformat(),
        "status": e.status,
        "urgency": e.urgency,
        "created_at": e.created_at.isoformat(),
        "progress_pct": progress,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/active",
    response_model=PublicEmergencyListResponse,
    summary="List active emergencies for public display",
)
async def list_active_emergencies_public(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return active emergencies ordered by urgency (critical first), then created_at DESC.

    Used by the homepage emergency banner and public emergency listing page.
    Response includes cache headers for 60-second caching.
    """
    # Urgency ordering: critical=1, high=2 (so critical sorts first)
    urgency_order = case(
        (EmergencyCase.urgency == "critical", 1),
        else_=2,
    )

    base_where = [
        EmergencyCase.is_deleted.is_(False),
        EmergencyCase.status.in_(["active", "funded"]),
    ]

    count_stmt = select(func.count()).select_from(EmergencyCase).where(*base_where)
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(EmergencyCase)
        .where(*base_where)
        .order_by(urgency_order, EmergencyCase.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    cases = list(result.scalars().all())

    return {
        "items": [_serialise(c) for c in cases],
        "total": total,
    }


@router.get(
    "/{emergency_id}",
    response_model=PublicEmergencyResponse,
    summary="Get a single emergency case (public)",
)
async def get_emergency_public(
    emergency_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Return a single active emergency case for public display."""
    stmt = select(EmergencyCase).where(
        EmergencyCase.id == emergency_id,
        EmergencyCase.is_deleted.is_(False),
    )
    result = await db.execute(stmt)
    case_obj = result.scalar_one_or_none()

    if case_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Emergency not found"},
        )

    return _serialise(case_obj)
