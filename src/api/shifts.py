"""Volunteer shift scheduling API (RAP-180, RAP-182, RAP-183).

Staff can create and manage shifts with time slots and capacity.
Staff can also record volunteer attendance (RAP-183).
Volunteers can view available shifts and self-signup (RAP-182).

Endpoints:
    POST   /api/shifts                              -- create shift (staff only)
    GET    /api/shifts                              -- list shifts (authenticated)
    GET    /api/shifts/roles                        -- list valid roles
    GET    /api/shifts/my-signups                   -- volunteer's own signups
    GET    /api/shifts/{id}                         -- get shift detail (authenticated)
    PATCH  /api/shifts/{id}                         -- update shift (staff only)
    DELETE /api/shifts/{id}                         -- cancel/delete shift (staff only)
    POST   /api/shifts/{id}/signup                  -- volunteer signs up for shift
    DELETE /api/shifts/{id}/signup                  -- volunteer cancels their signup
    GET    /api/shifts/{id}/signups                 -- list signups for shift (staff)
    PATCH  /api/shifts/{id}/signups/{signup_id}     -- update attendance (staff)
"""

import logging
from datetime import date, datetime, time
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user as get_current_user
from src.auth.dependencies import require_staff
from src.db.models.shift import (
    SHIFT_CAPACITY_MAX,
    SHIFT_CAPACITY_MIN,
    VALID_SHIFT_ROLES,
    VALID_SHIFT_STATUSES,
    Shift,
    ShiftRole,
    ShiftSignup,
    ShiftStatus,
)
from src.db.models.user import User
from src.db.session import get_db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

staff_router = APIRouter(tags=["Shifts"])
public_router = APIRouter(tags=["Shifts"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ShiftCreateRequest(BaseModel):
    """Payload for creating a new shift."""

    shift_date: date = Field(..., description="Date of the shift (YYYY-MM-DD)")
    start_time: time = Field(..., description="Shift start time (HH:MM)")
    end_time: time = Field(..., description="Shift end time (HH:MM)")
    role: ShiftRole = Field(default=ShiftRole.GENERAL, description="Type of work for this shift")
    capacity: int = Field(
        default=1,
        ge=SHIFT_CAPACITY_MIN,
        le=SHIFT_CAPACITY_MAX,
        description="Maximum number of volunteers for this shift",
    )
    title: str | None = Field(None, max_length=200, description="Optional short title")
    notes: str | None = Field(None, description="Additional notes for volunteers")
    location: str | None = Field(None, max_length=200, description="Where the shift takes place")

    @model_validator(mode="after")
    def end_after_start(self) -> "ShiftCreateRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ShiftUpdateRequest(BaseModel):
    """Payload for updating an existing shift."""

    shift_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    role: ShiftRole | None = None
    capacity: int | None = Field(None, ge=SHIFT_CAPACITY_MIN, le=SHIFT_CAPACITY_MAX)
    title: str | None = Field(None, max_length=200)
    notes: str | None = None
    location: str | None = Field(None, max_length=200)
    status: ShiftStatus | None = None

    @model_validator(mode="after")
    def end_after_start_if_both_provided(self) -> "ShiftUpdateRequest":
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            raise ValueError("end_time must be after start_time")
        return self


class ShiftResponse(BaseModel):
    """Shift detail response."""

    id: UUID
    created_by: UUID
    shift_date: date
    start_time: time
    end_time: time
    role: str
    capacity: int
    slots_filled: int
    status: str
    title: str | None = None
    notes: str | None = None
    location: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShiftListResponse(BaseModel):
    """Paginated list of shifts."""

    items: list[ShiftResponse]
    total: int
    page: int
    page_size: int


class ShiftRolesResponse(BaseModel):
    """Available shift role options."""

    roles: list[str]


class ShiftSignupResponse(BaseModel):
    """A volunteer's signup record for a shift."""

    id: UUID
    shift_id: UUID
    volunteer_id: UUID
    confirmed: bool
    attended: bool | None = None
    signed_up_at: datetime
    notes: str | None = None

    model_config = {"from_attributes": True}


class MySignupsResponse(BaseModel):
    """List of the authenticated volunteer's shift signups."""

    items: list[ShiftSignupResponse]
    total: int


# ---------------------------------------------------------------------------
# Endpoints — Public (read-only, authenticated)
# ---------------------------------------------------------------------------


@public_router.get("/api/shifts/roles", response_model=ShiftRolesResponse)
async def list_shift_roles() -> ShiftRolesResponse:
    """Return all valid shift role values."""
    return ShiftRolesResponse(roles=sorted(VALID_SHIFT_ROLES))


@public_router.get("/api/shifts", response_model=ShiftListResponse)
async def list_shifts(
    shift_date: date | None = Query(None, description="Filter by exact date"),
    date_from: date | None = Query(None, description="Filter shifts from this date"),
    date_to: date | None = Query(None, description="Filter shifts up to this date"),
    role: ShiftRole | None = Query(None, description="Filter by role"),
    shift_status: str | None = Query(None, description="Filter by status (open, full, etc.)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> ShiftListResponse:
    """List shifts with optional filters. Requires authentication."""
    if shift_status and shift_status not in VALID_SHIFT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status. Must be one of: {sorted(VALID_SHIFT_STATUSES)}",
        )

    filters = []
    if shift_date:
        filters.append(Shift.shift_date == shift_date)
    if date_from:
        filters.append(Shift.shift_date >= date_from)
    if date_to:
        filters.append(Shift.shift_date <= date_to)
    if role:
        filters.append(Shift.role == role.value)
    if shift_status:
        filters.append(Shift.status == shift_status)

    count_stmt = select(func.count()).select_from(Shift)
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    stmt = select(Shift).order_by(Shift.shift_date, Shift.start_time)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    shifts = result.scalars().all()

    return ShiftListResponse(
        items=[ShiftResponse.model_validate(s) for s in shifts],
        total=total,
        page=page,
        page_size=page_size,
    )


@public_router.get("/api/shifts/{shift_id}", response_model=ShiftResponse)
async def get_shift(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> ShiftResponse:
    """Get a single shift by ID. Requires authentication."""
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if shift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shift {shift_id} not found",
        )
    return ShiftResponse.model_validate(shift)


# ---------------------------------------------------------------------------
# Endpoints — Volunteer self-signup (RAP-182, authenticated)
# ---------------------------------------------------------------------------

SIGNUP_BLOCKED_STATUSES = {ShiftStatus.CANCELLED.value, ShiftStatus.COMPLETED.value}


@public_router.get("/api/shifts/my-signups", response_model=MySignupsResponse)
async def get_my_signups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MySignupsResponse:
    """Return all shift signups for the authenticated user."""
    stmt = select(ShiftSignup).where(ShiftSignup.volunteer_id == current_user.id)
    result = await db.execute(stmt)
    signups = result.scalars().all()
    return MySignupsResponse(
        items=[ShiftSignupResponse.model_validate(s) for s in signups],
        total=len(signups),
    )


@public_router.post(
    "/api/shifts/{shift_id}/signup",
    response_model=ShiftSignupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup_for_shift(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ShiftSignupResponse:
    """Volunteer signs up for an open shift.

    Rules:
    - Shift must be open (not full, cancelled, or completed)
    - Volunteer cannot sign up more than once for the same shift
    - slots_filled increments atomically; shift transitions to full if capacity reached
    """
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if shift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shift {shift_id} not found",
        )

    if shift.status in SIGNUP_BLOCKED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot sign up for a {shift.status} shift",
        )

    if shift.status == ShiftStatus.FULL.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Shift is full — no more spots available",
        )

    existing = await db.execute(
        select(ShiftSignup).where(
            ShiftSignup.shift_id == shift_id,
            ShiftSignup.volunteer_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already signed up for this shift",
        )

    signup = ShiftSignup(shift_id=shift_id, volunteer_id=current_user.id)
    db.add(signup)

    # Atomic increment — checked by DB constraint (slots_filled <= capacity)
    await db.execute(
        sa.update(Shift).where(Shift.id == shift_id).values(slots_filled=Shift.slots_filled + 1)
    )
    await db.refresh(shift)

    if shift.slots_filled >= shift.capacity:
        shift.status = ShiftStatus.FULL.value

    await db.commit()
    await db.refresh(signup)
    logger.info(
        "Volunteer signed up for shift",
        extra={"shift_id": str(shift_id), "volunteer_id": str(current_user.id)},
    )
    return ShiftSignupResponse.model_validate(signup)


@public_router.delete("/api/shifts/{shift_id}/signup", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_shift_signup(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Volunteer cancels their own signup for a shift.

    Rules:
    - Volunteer can only cancel their own signup
    - Cannot cancel if shift is completed
    - slots_filled decrements; shift transitions back to open if it was full
    """
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if shift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shift {shift_id} not found",
        )

    if shift.status == ShiftStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot cancel signup for a completed shift",
        )

    signup_result = await db.execute(
        select(ShiftSignup).where(
            ShiftSignup.shift_id == shift_id,
            ShiftSignup.volunteer_id == current_user.id,
        )
    )
    signup = signup_result.scalar_one_or_none()
    if signup is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No signup found for this shift",
        )

    await db.delete(signup)
    await db.execute(
        sa.update(Shift)
        .where(Shift.id == shift_id)
        .values(slots_filled=sa.func.greatest(Shift.slots_filled - 1, 0))
    )
    await db.refresh(shift)

    if shift.status == ShiftStatus.FULL.value and shift.slots_filled < shift.capacity:
        shift.status = ShiftStatus.OPEN.value

    await db.commit()
    logger.info(
        "Volunteer cancelled shift signup",
        extra={"shift_id": str(shift_id), "volunteer_id": str(current_user.id)},
    )


# ---------------------------------------------------------------------------
# Endpoints — Staff only (write operations)
# ---------------------------------------------------------------------------


@staff_router.post("/api/shifts", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
async def create_shift(
    body: ShiftCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> ShiftResponse:
    """Create a new shift. Staff only."""
    shift = Shift(
        created_by=current_user.id,
        shift_date=body.shift_date,
        start_time=body.start_time,
        end_time=body.end_time,
        role=body.role.value,
        capacity=body.capacity,
        slots_filled=0,
        status=ShiftStatus.OPEN.value,
        title=body.title,
        notes=body.notes,
        location=body.location,
    )
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    logger.info(
        "Shift created", extra={"shift_id": str(shift.id), "staff_id": str(current_user.id)}
    )
    return ShiftResponse.model_validate(shift)


@staff_router.patch("/api/shifts/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: UUID,
    body: ShiftUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> ShiftResponse:
    """Update a shift. Staff only."""
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if shift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shift {shift_id} not found",
        )

    if shift.status == ShiftStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot modify a completed shift",
        )

    update_data = body.model_dump(exclude_unset=True)

    # Validate capacity against current signups if reducing
    if "capacity" in update_data and update_data["capacity"] < shift.slots_filled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot reduce capacity below current signups ({shift.slots_filled})",
        )

    # Validate time consistency when only one of start/end is updated
    new_start = update_data.get("start_time", shift.start_time)
    new_end = update_data.get("end_time", shift.end_time)
    if new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_time must be after start_time",
        )

    for field, value in update_data.items():
        if (field == "role" and isinstance(value, ShiftRole)) or (
            field == "status" and isinstance(value, ShiftStatus)
        ):
            setattr(shift, field, value.value)
        else:
            setattr(shift, field, value)

    # Auto-update status based on capacity
    if shift.status == ShiftStatus.OPEN.value and shift.slots_filled >= shift.capacity:
        shift.status = ShiftStatus.FULL.value
    elif shift.status == ShiftStatus.FULL.value and shift.slots_filled < shift.capacity:
        shift.status = ShiftStatus.OPEN.value

    await db.commit()
    await db.refresh(shift)
    logger.info(
        "Shift updated", extra={"shift_id": str(shift_id), "staff_id": str(current_user.id)}
    )
    return ShiftResponse.model_validate(shift)


@staff_router.delete("/api/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    """Cancel and delete a shift. Staff only."""
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if shift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shift {shift_id} not found",
        )

    if shift.status == ShiftStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a completed shift",
        )

    await db.delete(shift)
    await db.commit()
    logger.info(
        "Shift deleted", extra={"shift_id": str(shift_id), "staff_id": str(current_user.id)}
    )


# ---------------------------------------------------------------------------
# Endpoints — Attendance tracking (RAP-183, staff only)
# ---------------------------------------------------------------------------


class ShiftSignupListResponse(BaseModel):
    """All signups for a given shift."""

    items: list[ShiftSignupResponse]
    total: int


class AttendanceUpdateRequest(BaseModel):
    """Payload for marking a volunteer's attendance."""

    attended: bool | None = Field(
        ...,
        description="true = attended, false = no-show, null = clear/unknown",
    )
    notes: str | None = Field(None, max_length=500, description="Optional staff note")


@staff_router.get("/api/shifts/{shift_id}/signups", response_model=ShiftSignupListResponse)
async def list_shift_signups(
    shift_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: User = Depends(require_staff),
) -> ShiftSignupListResponse:
    """List all volunteer signups for a shift. Staff only."""
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shift {shift_id} not found",
        )

    signup_result = await db.execute(
        select(ShiftSignup)
        .where(ShiftSignup.shift_id == shift_id)
        .order_by(ShiftSignup.signed_up_at)
    )
    signups = signup_result.scalars().all()
    return ShiftSignupListResponse(
        items=[ShiftSignupResponse.model_validate(s) for s in signups],
        total=len(signups),
    )


@staff_router.patch(
    "/api/shifts/{shift_id}/signups/{signup_id}",
    response_model=ShiftSignupResponse,
)
async def update_signup_attendance(
    shift_id: UUID,
    signup_id: UUID,
    body: AttendanceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: User = Depends(require_staff),
) -> ShiftSignupResponse:
    """Mark a volunteer as attended or no-show for a shift. Staff only.

    The shift does not need to be in 'completed' status — staff can record
    attendance for any past shift. Notes are optional.
    """
    shift_result = await db.execute(select(Shift).where(Shift.id == shift_id))
    if shift_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shift {shift_id} not found",
        )

    signup_result = await db.execute(
        select(ShiftSignup).where(
            ShiftSignup.id == signup_id,
            ShiftSignup.shift_id == shift_id,
        )
    )
    signup = signup_result.scalar_one_or_none()
    if signup is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signup {signup_id} not found for shift {shift_id}",
        )

    signup.attended = body.attended
    if body.notes is not None:
        signup.notes = body.notes

    await db.commit()
    await db.refresh(signup)
    logger.info(
        "Attendance updated",
        extra={
            "shift_id": str(shift_id),
            "signup_id": str(signup_id),
            "attended": body.attended,
            "staff_id": str(current_staff.id),
        },
    )
    return ShiftSignupResponse.model_validate(signup)
