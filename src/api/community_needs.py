"""Community needs endpoints — public listing and admin management.

Endpoints:
  GET  /api/community/needs           — list open needs (public)
  GET  /api/community/needs/{id}      — get need detail (public)
  POST /api/admin/community-needs     — create a need (staff)
  PATCH /api/admin/community-needs/{id} — update a need (staff)
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.community_need import CommunityNeed, NeedCategory, NeedStatus
from src.db.models.user import User
from src.db.session import get_db

logger = logging.getLogger(__name__)

# --- Schemas ---


class NeedCreateRequest(BaseModel):
    """Request schema for creating a community need."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    category: NeedCategory = NeedCategory.OTHER
    estimated_cost_cents: int = Field(..., gt=0)
    currency: str = Field("USD", pattern=r"^(USD|EUR|PYG)$")
    image_url: str | None = None


class NeedUpdateRequest(BaseModel):
    """Request schema for updating a community need."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1)
    category: NeedCategory | None = None
    estimated_cost_cents: int | None = Field(None, gt=0)
    status: NeedStatus | None = None
    image_url: str | None = None


class NeedResponse(BaseModel):
    """Response schema for a community need."""

    id: UUID
    title: str
    description: str
    category: str
    status: str
    estimated_cost_cents: int
    current_raised_cents: int
    currency: str
    donor_count: int
    creator_id: UUID
    image_url: str | None
    progress_percent: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NeedListResponse(BaseModel):
    """Paginated list of community needs."""

    items: list[NeedResponse]
    total: int


# --- Helpers ---


def _to_response(need: CommunityNeed) -> NeedResponse:
    """Convert ORM model to response, computing progress percent."""
    progress = 0.0
    if need.estimated_cost_cents > 0:
        progress = min(
            100.0,
            round(need.current_raised_cents / need.estimated_cost_cents * 100, 1),
        )
    return NeedResponse(
        id=need.id,
        title=need.title,
        description=need.description,
        category=need.category,
        status=need.status,
        estimated_cost_cents=need.estimated_cost_cents,
        current_raised_cents=need.current_raised_cents,
        currency=need.currency,
        donor_count=need.donor_count,
        creator_id=need.creator_id,
        image_url=need.image_url,
        progress_percent=progress,
        created_at=need.created_at,
        updated_at=need.updated_at,
    )


# --- Public router ---

public_router = APIRouter(
    prefix="/api/community/needs",
    tags=["community-needs"],
)


@public_router.get(
    "",
    response_model=NeedListResponse,
    summary="List open community needs",
)
async def list_needs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: NeedCategory | None = None,
    db: AsyncSession = Depends(get_db),
) -> NeedListResponse:
    """List open community needs for the public needs board."""
    query = select(CommunityNeed).where(
        CommunityNeed.status == NeedStatus.OPEN,
    )
    count_query = (
        select(func.count())
        .select_from(CommunityNeed)
        .where(
            CommunityNeed.status == NeedStatus.OPEN,
        )
    )

    if category is not None:
        query = query.where(CommunityNeed.category == category)
        count_query = count_query.where(CommunityNeed.category == category)

    query = query.order_by(CommunityNeed.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    needs = list(result.scalars().all())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    return NeedListResponse(
        items=[_to_response(n) for n in needs],
        total=total,
    )


@public_router.get(
    "/{need_id}",
    response_model=NeedResponse,
    summary="Get community need detail",
)
async def get_need(
    need_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> NeedResponse:
    """Get a single community need by ID (public)."""
    need = await db.get(CommunityNeed, need_id)
    if need is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Necesidad no encontrada"},
        )
    return _to_response(need)


# --- Admin router ---

admin_router = APIRouter(
    prefix="/api/admin/community-needs",
    tags=["admin-community-needs"],
)


@admin_router.post(
    "",
    response_model=NeedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a community need",
)
async def create_need(
    body: NeedCreateRequest,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> NeedResponse:
    """Create a new community need (staff only)."""
    need = CommunityNeed(
        title=body.title,
        description=body.description,
        category=body.category,
        estimated_cost_cents=body.estimated_cost_cents,
        currency=body.currency,
        image_url=body.image_url,
        creator_id=current_user.id,
    )
    db.add(need)
    await db.commit()
    await db.refresh(need)
    logger.info("Community need created: %s by user %s", need.id, current_user.id)
    return _to_response(need)


@admin_router.patch(
    "/{need_id}",
    response_model=NeedResponse,
    summary="Update a community need",
)
async def update_need(
    need_id: UUID,
    body: NeedUpdateRequest,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> NeedResponse:
    """Update a community need (staff only)."""
    need = await db.get(CommunityNeed, need_id)
    if need is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Necesidad no encontrada"},
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(need, field, value)

    await db.commit()
    await db.refresh(need)
    logger.info("Community need updated: %s by user %s", need.id, current_user.id)
    return _to_response(need)


@admin_router.get(
    "",
    response_model=NeedListResponse,
    summary="List all community needs (admin)",
)
async def admin_list_needs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    need_status: NeedStatus | None = None,
    current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> NeedListResponse:
    """List all community needs with optional status filter (staff only)."""
    query = select(CommunityNeed)
    count_query = select(func.count()).select_from(CommunityNeed)

    if need_status is not None:
        query = query.where(CommunityNeed.status == need_status)
        count_query = count_query.where(CommunityNeed.status == need_status)

    query = query.order_by(CommunityNeed.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    needs = list(result.scalars().all())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    return NeedListResponse(
        items=[_to_response(n) for n in needs],
        total=total,
    )
