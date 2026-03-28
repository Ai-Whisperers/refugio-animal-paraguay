"""Emergency update endpoints -- post progress updates on emergency cases.

Endpoints:
  POST /api/emergencies/{emergency_id}/updates    -- create update (staff)
  GET  /api/emergencies/{emergency_id}/updates     -- list updates (staff)
  GET  /api/public/emergencies/{emergency_id}/updates -- public update timeline
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.emergency_case import EmergencyCase
from src.db.models.emergency_update import EmergencyOutcome, EmergencyUpdate
from src.db.models.user import User
from src.db.session import get_async_session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

VALID_OUTCOMES = [o.value for o in EmergencyOutcome]


class EmergencyUpdateCreateRequest(BaseModel):
    """Request body for creating an emergency update."""

    text: str = Field(..., min_length=1, max_length=1000)
    photos: list[str] = Field(default_factory=list, max_length=3)
    is_resolution: bool = False
    outcome: str | None = Field(
        default=None,
        description=f"Required when is_resolution=True. One of: {', '.join(VALID_OUTCOMES)}",
    )


class EmergencyUpdateResponse(BaseModel):
    """Response schema for an emergency update."""

    id: UUID
    emergency_id: UUID
    text: str
    photos: list[str]
    posted_by: UUID | None = None
    is_resolution: bool
    outcome: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class EmergencyUpdateListResponse(BaseModel):
    """Paginated list of emergency updates."""

    items: list[EmergencyUpdateResponse]
    total: int


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

staff_router = APIRouter(
    prefix="/api/emergencies",
    tags=["emergency-updates"],
    dependencies=[Depends(require_staff)],
)

public_router = APIRouter(
    prefix="/api/public/emergencies",
    tags=["emergency-updates-public"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialise_update(update: EmergencyUpdate) -> dict:
    """Convert an EmergencyUpdate ORM object to a response dict."""
    return {
        "id": update.id,
        "emergency_id": update.emergency_id,
        "text": update.text,
        "photos": update.photos or [],
        "posted_by": update.posted_by,
        "is_resolution": update.is_resolution,
        "outcome": update.outcome,
        "created_at": update.created_at.isoformat(),
    }


async def _verify_emergency_exists(emergency_id: UUID, db: AsyncSession) -> EmergencyCase:
    """Raise 404 if emergency case doesn't exist or is deleted."""
    stmt = select(EmergencyCase).where(
        EmergencyCase.id == emergency_id,
        EmergencyCase.is_deleted.is_(False),
    )
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Emergency case not found", "emergency_id": str(emergency_id)},
        )
    return case


# ---------------------------------------------------------------------------
# Staff endpoints
# ---------------------------------------------------------------------------


@staff_router.post(
    "/{emergency_id}/updates",
    response_model=EmergencyUpdateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post an update on an emergency case",
)
async def create_emergency_update(
    emergency_id: UUID,
    body: EmergencyUpdateCreateRequest,
    user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a progress update for an emergency case.

    When is_resolution is True, the emergency case status is set to 'closed'.
    """
    case = await _verify_emergency_exists(emergency_id, db)

    # Validate resolution fields
    if body.is_resolution:
        if not body.outcome:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "outcome is required when is_resolution is True"},
            )
        if body.outcome not in VALID_OUTCOMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Invalid outcome. Must be one of: {', '.join(VALID_OUTCOMES)}",
                },
            )

    # Limit photos to 3
    photos = body.photos[:3] if body.photos else []

    update = EmergencyUpdate(
        emergency_id=emergency_id,
        text=body.text,
        photos=photos,
        posted_by=user.id,
        is_resolution=body.is_resolution,
        outcome=body.outcome if body.is_resolution else None,
    )
    db.add(update)

    # If this is a resolution, close the emergency case
    if body.is_resolution:
        case.status = "closed"

    await db.commit()
    await db.refresh(update)
    return _serialise_update(update)


@staff_router.get(
    "/{emergency_id}/updates",
    response_model=EmergencyUpdateListResponse,
    summary="List updates for an emergency case",
)
async def list_emergency_updates(
    emergency_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """List all updates for an emergency case, most recent first."""
    await _verify_emergency_exists(emergency_id, db)

    count_stmt = (
        select(func.count())
        .select_from(EmergencyUpdate)
        .where(EmergencyUpdate.emergency_id == emergency_id)
    )
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(EmergencyUpdate)
        .where(EmergencyUpdate.emergency_id == emergency_id)
        .order_by(EmergencyUpdate.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    updates = list(result.scalars().all())

    return {
        "items": [_serialise_update(u) for u in updates],
        "total": total,
    }


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@public_router.get(
    "/{emergency_id}/updates",
    response_model=EmergencyUpdateListResponse,
    summary="Public timeline of emergency updates",
)
async def list_public_emergency_updates(
    emergency_id: UUID,
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Public-facing timeline of updates for an emergency case."""
    await _verify_emergency_exists(emergency_id, db)

    count_stmt = (
        select(func.count())
        .select_from(EmergencyUpdate)
        .where(EmergencyUpdate.emergency_id == emergency_id)
    )
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = (
        select(EmergencyUpdate)
        .where(EmergencyUpdate.emergency_id == emergency_id)
        .order_by(EmergencyUpdate.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    updates = list(result.scalars().all())

    return {
        "items": [_serialise_update(u) for u in updates],
        "total": total,
    }
