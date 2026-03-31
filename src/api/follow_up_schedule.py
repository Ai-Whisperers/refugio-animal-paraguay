"""Post-adoption follow-up schedule management API (RAP-261, EPIC-53).

Staff endpoints for schedule visibility and maintenance.

Endpoints:
  GET  /api/admin/follow-ups/schedule/due              — pending follow-ups due soon
  GET  /api/admin/follow-ups/schedule/overdue           — all past-due pending follow-ups
  GET  /api/admin/adoptions/{request_id}/follow-up-schedule — per-adoption schedule
  POST /api/admin/follow-ups/schedule/mark-overdue      — bulk mark overdue
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.follow_up_schedule_service import (
    DEFAULT_DUE_WINDOW_DAYS,
    MAX_DUE_WINDOW_DAYS,
    FollowUpScheduleItem,
    MarkOverdueResult,
    get_due_follow_ups,
    get_overdue_follow_ups,
    get_schedule_for_adoption,
    mark_overdue_follow_ups,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/follow-ups/schedule",
    tags=["follow-up-schedule"],
)

adoption_schedule_router = APIRouter(
    prefix="/api/admin/adoptions",
    tags=["follow-up-schedule"],
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ScheduleItemResponse(BaseModel):
    id: UUID
    adoption_request_id: UUID
    scheduled_date: datetime
    day_offset: int
    status: str
    days_until_due: int
    is_overdue: bool

    model_config = {"from_attributes": True}


class MarkOverdueResponse(BaseModel):
    marked_count: int
    run_at: str


def _item_to_response(item: FollowUpScheduleItem) -> ScheduleItemResponse:
    return ScheduleItemResponse(
        id=item.id,
        adoption_request_id=item.adoption_request_id,
        scheduled_date=item.scheduled_date,
        day_offset=item.day_offset,
        status=item.status,
        days_until_due=item.days_until_due,
        is_overdue=item.is_overdue,
    )


def _mark_result_to_response(result: MarkOverdueResult) -> MarkOverdueResponse:
    return MarkOverdueResponse(
        marked_count=result.marked_count,
        run_at=result.run_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/due",
    response_model=list[ScheduleItemResponse],
    summary="Pending follow-ups due within N days",
)
async def get_due(
    within_days: int = Query(
        default=DEFAULT_DUE_WINDOW_DAYS,
        ge=1,
        le=MAX_DUE_WINDOW_DAYS,
        description="Lookahead window in days (default: 7, max: 90)",
    ),
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleItemResponse]:
    """Return pending follow-ups scheduled within the next `within_days` days.

    Auth: requires staff or admin role.
    """
    items = await get_due_follow_ups(db, within_days=within_days)
    return [_item_to_response(i) for i in items]


@router.get(
    "/overdue",
    response_model=list[ScheduleItemResponse],
    summary="Past-due pending follow-ups",
)
async def get_overdue(
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleItemResponse]:
    """Return all pending follow-ups whose scheduled date has passed.

    Auth: requires staff or admin role.
    """
    items = await get_overdue_follow_ups(db)
    return [_item_to_response(i) for i in items]


@router.post(
    "/mark-overdue",
    response_model=MarkOverdueResponse,
    summary="Bulk-mark past-due follow-ups as OVERDUE",
)
async def bulk_mark_overdue(
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> MarkOverdueResponse:
    """Update all past-due pending follow-ups to OVERDUE status.

    Idempotent — safe to call repeatedly. Returns the number of records updated.

    Auth: requires staff or admin role.
    """
    result = await mark_overdue_follow_ups(db)
    return _mark_result_to_response(result)


@adoption_schedule_router.get(
    "/{adoption_request_id}/follow-up-schedule",
    response_model=list[ScheduleItemResponse],
    summary="Per-adoption follow-up schedule",
)
async def get_adoption_schedule(
    adoption_request_id: UUID,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleItemResponse]:
    """Return the full follow-up schedule for a specific adoption.

    Items are ordered by day_offset (7d, 30d, 90d, 365d).

    Auth: requires staff or admin role.
    """
    items = await get_schedule_for_adoption(db, adoption_request_id)
    return [_item_to_response(i) for i in items]
