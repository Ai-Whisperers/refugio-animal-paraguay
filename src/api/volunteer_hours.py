"""Volunteer hours logging and tracking API (RAP-195).

Volunteers can log hours for activities performed outside of structured shifts.
Staff can view, filter, and approve logged hours.

Endpoints:
    POST /api/volunteers/hours                    -- log hours (authenticated volunteer)
    GET  /api/volunteers/hours/me                 -- own hour logs (authenticated volunteer)
    GET  /api/volunteers/hours/me/summary         -- own total hours summary
    GET  /api/staff/volunteer-hours               -- all hours logs (staff only)
    GET  /api/staff/volunteer-hours/{volunteer_id} -- hours for one volunteer (staff only)
    PUT  /api/staff/volunteer-hours/{log_id}/approve -- approve a log entry (staff only)
"""

import logging
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user as get_current_user
from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.models.volunteer_hours import (
    HOURS_MAX_DURATION,
    HOURS_MIN_DURATION,
    VALID_HOUR_CATEGORIES,
    VolunteerHoursLog,
)
from src.db.models.volunteer_profile import VolunteerProfile, VolunteerStatus
from src.db.session import get_db

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

public_router = APIRouter(prefix="/api/volunteers/hours", tags=["volunteer-hours"])
staff_router = APIRouter(prefix="/api/staff/volunteer-hours", tags=["volunteer-hours-staff"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class HoursLogCreateRequest(BaseModel):
    """Volunteer payload to log hours worked."""

    activity_date: date = Field(..., description="Date the activity was performed")
    duration_hours: float = Field(
        ...,
        ge=HOURS_MIN_DURATION,
        le=HOURS_MAX_DURATION,
        description="Duration in hours (min 0.25, max 24.0)",
    )
    category: str = Field(..., description="Category of the activity")
    description: str | None = Field(
        None,
        max_length=1000,
        description="Optional description of the activity performed",
    )
    shift_id: UUID | None = Field(
        None,
        description="Optional shift ID if the hours are linked to a specific shift",
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_HOUR_CATEGORIES:
            raise ValueError(
                f"Invalid category '{v}'. Must be one of: {sorted(VALID_HOUR_CATEGORIES)}"
            )
        return v

    @field_validator("activity_date")
    @classmethod
    def validate_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Activity date cannot be in the future")
        return v


class HoursLogResponse(BaseModel):
    """A volunteer hours log entry as returned by the API."""

    id: UUID
    volunteer_id: UUID
    activity_date: date
    duration_hours: float
    category: str
    description: str | None
    shift_id: UUID | None
    approved: bool
    approved_by: UUID | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HoursLogListResponse(BaseModel):
    """Paginated list of hours log entries."""

    items: list[HoursLogResponse]
    total: int
    page: int
    page_size: int


class HoursSummaryResponse(BaseModel):
    """Summary of volunteer hours totals."""

    volunteer_id: UUID
    total_hours: float
    approved_hours: float
    pending_hours: float
    hours_by_category: dict[str, float]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_response(log: VolunteerHoursLog) -> HoursLogResponse:
    """Convert ORM object to response schema."""
    return HoursLogResponse(
        id=log.id,
        volunteer_id=log.volunteer_id,
        activity_date=log.activity_date,
        duration_hours=float(log.duration_hours),
        category=log.category,
        description=log.description,
        shift_id=log.shift_id,
        approved=log.approved,
        approved_by=log.approved_by,
        approved_at=log.approved_at,
        created_at=log.created_at,
        updated_at=log.updated_at,
    )


async def _get_approved_profile(db: AsyncSession, user_id: UUID) -> VolunteerProfile:
    """Return the approved VolunteerProfile for the given user, or raise 403/404."""
    result = await db.execute(select(VolunteerProfile).where(VolunteerProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No volunteer profile found. Submit an application first.",
        )
    if profile.status != VolunteerStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only approved volunteers can log hours.",
        )
    return profile


# ---------------------------------------------------------------------------
# Endpoints — Volunteer (authenticated)
# ---------------------------------------------------------------------------


@public_router.post(
    "",
    response_model=HoursLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log volunteer hours",
)
async def log_hours(
    body: HoursLogCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Log hours for a volunteer activity.

    Requires an approved volunteer profile.
    Returns 403 if the profile is not approved.
    Returns 404 if no profile exists.
    """
    profile = await _get_approved_profile(db, current_user.id)

    log_entry = VolunteerHoursLog(
        volunteer_id=profile.id,
        activity_date=body.activity_date,
        duration_hours=body.duration_hours,
        category=body.category,
        description=body.description,
        shift_id=body.shift_id,
    )
    db.add(log_entry)
    await db.flush()
    await db.refresh(log_entry)

    logger.info(
        "Volunteer hours logged: volunteer=%s, date=%s, hours=%.2f, category=%s",
        str(profile.id)[:8] + "...",
        body.activity_date,
        body.duration_hours,
        body.category,
    )
    return _to_response(log_entry)


@public_router.get(
    "/me",
    response_model=HoursLogListResponse,
    summary="List own volunteer hour logs",
)
async def list_my_hours(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    category: str | None = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return own hour logs, most recent first.

    Optionally filter by category.
    """
    profile = await _get_approved_profile(db, current_user.id)

    base_query = select(VolunteerHoursLog).where(VolunteerHoursLog.volunteer_id == profile.id)
    if category:
        base_query = base_query.where(VolunteerHoursLog.category == category)

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()

    items_result = await db.execute(
        base_query.order_by(VolunteerHoursLog.activity_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = items_result.scalars().all()

    return HoursLogListResponse(
        items=[_to_response(log) for log in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@public_router.get(
    "/me/summary",
    response_model=HoursSummaryResponse,
    summary="Get own volunteer hours summary",
)
async def get_my_hours_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return a summary of own total, approved, and pending hours broken down by category."""
    profile = await _get_approved_profile(db, current_user.id)

    logs_result = await db.execute(
        select(VolunteerHoursLog).where(VolunteerHoursLog.volunteer_id == profile.id)
    )
    logs = logs_result.scalars().all()

    total = sum(float(log.duration_hours) for log in logs)
    approved = sum(float(log.duration_hours) for log in logs if log.approved)
    pending = total - approved

    by_category: dict[str, float] = {}
    for log in logs:
        by_category[log.category] = by_category.get(log.category, 0.0) + float(log.duration_hours)

    return HoursSummaryResponse(
        volunteer_id=profile.id,
        total_hours=round(total, 2),
        approved_hours=round(approved, 2),
        pending_hours=round(pending, 2),
        hours_by_category={k: round(v, 2) for k, v in by_category.items()},
    )


# ---------------------------------------------------------------------------
# Endpoints — Staff
# ---------------------------------------------------------------------------


@staff_router.get(
    "",
    response_model=HoursLogListResponse,
    summary="List all volunteer hour logs (staff only)",
)
async def list_all_hours(
    volunteer_id: UUID | None = Query(None, description="Filter by volunteer profile ID"),
    category: str | None = Query(None, description="Filter by category"),
    approved: bool | None = Query(None, description="Filter by approval status"),
    date_from: date | None = Query(None, description="Filter logs from this date"),
    date_to: date | None = Query(None, description="Filter logs up to this date"),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> Any:
    """Return paginated hour logs with optional filters. Staff only."""
    base_query = select(VolunteerHoursLog)
    if volunteer_id:
        base_query = base_query.where(VolunteerHoursLog.volunteer_id == volunteer_id)
    if category:
        base_query = base_query.where(VolunteerHoursLog.category == category)
    if approved is not None:
        base_query = base_query.where(VolunteerHoursLog.approved == approved)
    if date_from:
        base_query = base_query.where(VolunteerHoursLog.activity_date >= date_from)
    if date_to:
        base_query = base_query.where(VolunteerHoursLog.activity_date <= date_to)

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()

    items_result = await db.execute(
        base_query.order_by(VolunteerHoursLog.activity_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = items_result.scalars().all()

    return HoursLogListResponse(
        items=[_to_response(log) for log in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@staff_router.get(
    "/{volunteer_id}",
    response_model=HoursSummaryResponse,
    summary="Get hours summary for a volunteer (staff only)",
)
async def get_volunteer_hours_summary(
    volunteer_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> Any:
    """Return hours summary for a specific volunteer. Staff only.

    Returns 404 if the volunteer profile does not exist.
    """
    profile_result = await db.execute(
        select(VolunteerProfile).where(VolunteerProfile.id == volunteer_id)
    )
    if profile_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer profile not found.",
        )

    logs_result = await db.execute(
        select(VolunteerHoursLog).where(VolunteerHoursLog.volunteer_id == volunteer_id)
    )
    logs = logs_result.scalars().all()

    total = sum(float(log.duration_hours) for log in logs)
    approved = sum(float(log.duration_hours) for log in logs if log.approved)
    pending = total - approved

    by_category: dict[str, float] = {}
    for log in logs:
        by_category[log.category] = by_category.get(log.category, 0.0) + float(log.duration_hours)

    return HoursSummaryResponse(
        volunteer_id=volunteer_id,
        total_hours=round(total, 2),
        approved_hours=round(approved, 2),
        pending_hours=round(pending, 2),
        hours_by_category={k: round(v, 2) for k, v in by_category.items()},
    )


@staff_router.put(
    "/{log_id}/approve",
    response_model=HoursLogResponse,
    summary="Approve a volunteer hours log entry (staff only)",
)
async def approve_hours_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> Any:
    """Mark a volunteer hours log entry as approved.

    Returns 404 if the log entry does not exist.
    Returns 422 if it is already approved.
    Staff only.
    """
    result = await db.execute(select(VolunteerHoursLog).where(VolunteerHoursLog.id == log_id))
    log_entry = result.scalar_one_or_none()
    if log_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hours log entry not found.",
        )
    if log_entry.approved:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Hours log entry is already approved.",
        )

    log_entry.approved = True
    log_entry.approved_by = current_user.id
    log_entry.approved_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(log_entry)

    logger.info(
        "Hours log %s approved by staff %s",
        str(log_id)[:8] + "...",
        str(current_user.id)[:8] + "...",
    )
    return _to_response(log_entry)
