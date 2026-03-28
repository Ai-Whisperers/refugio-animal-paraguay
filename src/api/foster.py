"""Foster family registration, approval, placement matching, and check-in API (RAP-190, RAP-191, RAP-192).

Any authenticated user can apply to become a foster family.
Staff can list applications, approve/reject them, use the placement matching
endpoints to find the best foster family for a given animal (or vice-versa),
and manage periodic welfare check-ins.

Endpoints:
    POST /api/foster/apply                                    -- submit foster application (authenticated)
    GET  /api/foster/me                                       -- get own foster profile (authenticated)
    GET  /api/staff/foster                                    -- list all applications (staff only)
    GET  /api/staff/foster/{id}                               -- get one application (staff only)
    PUT  /api/staff/foster/{id}/review                        -- approve/reject application (staff only)
    GET  /api/staff/foster/match/{animal_id}                  -- ranked foster families for an animal (staff only)
    GET  /api/staff/foster/{id}/matches                       -- ranked animals for a foster family (staff only)
    POST /api/staff/foster/placements/{placement_id}/check-ins           -- schedule a check-in (staff only)
    GET  /api/staff/foster/placements/{placement_id}/check-ins           -- list check-ins for placement (staff only)
    PUT  /api/staff/foster/check-ins/{check_in_id}/complete              -- complete a check-in (staff only)
    PUT  /api/staff/foster/check-ins/{check_in_id}/cancel                -- cancel a check-in (staff only)
    POST /api/staff/foster/check-ins/{check_in_id}/remind                -- log reminder dispatch (staff only)
    GET  /api/staff/foster/check-ins/upcoming                            -- upcoming/overdue check-ins (staff only)
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user as get_current_user
from src.auth.dependencies import require_staff
from src.db.models.foster_check_in import (
    CHECK_IN_NOTES_MAX_LENGTH,
    DEFAULT_INTERVAL_DAYS,
    MAX_INTERVAL_DAYS,
    MIN_INTERVAL_DAYS,
    CheckInStatus,
    CheckInType,
    FosterCheckIn,
)
from src.db.models.foster_profile import (
    ANIMAL_TYPE_PREFERENCE_VALUES,
    FOSTER_MOTIVATION_MAX_LENGTH,
    FOSTER_MOTIVATION_MIN_LENGTH,
    AnimalTypePreference,
    FosterProfile,
    FosterStatus,
    HomeType,
)
from src.db.models.user import User
from src.db.session import get_db
from src.services.foster_check_in_service import (
    UPCOMING_WINDOW_DAYS,
    cancel_check_in,
    complete_check_in,
    create_check_in,
    list_check_ins_for_placement,
    list_upcoming_check_ins,
    record_reminder_sent,
)
from src.services.foster_placement_service import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    find_animal_matches_for_foster,
    find_foster_matches_for_animal,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

public_router = APIRouter(tags=["Foster"])
staff_router = APIRouter(tags=["Foster"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class FosterApplyRequest(BaseModel):
    """Payload for submitting a foster family application."""

    motivation: str = Field(
        ...,
        min_length=FOSTER_MOTIVATION_MIN_LENGTH,
        max_length=FOSTER_MOTIVATION_MAX_LENGTH,
        description="Why the applicant wants to foster animals",
    )
    experience_description: str | None = Field(
        None,
        max_length=2000,
        description="Prior experience with animals",
    )
    home_type: HomeType = Field(
        default=HomeType.APARTMENT,
        description="Type of housing",
    )
    has_outdoor_space: bool = Field(
        default=False,
        description="Whether the home has outdoor space (yard, garden, etc.)",
    )
    has_other_pets: bool = Field(
        default=False,
        description="Whether the household already has pets",
    )
    other_pets_description: str | None = Field(
        None,
        max_length=500,
        description="Description of existing pets if any",
    )
    max_animals: int = Field(
        default=1,
        ge=1,
        le=20,
        description="Maximum number of animals the family can foster at once",
    )
    preferred_animal_types: list[AnimalTypePreference] = Field(
        default_factory=list,
        description="Types of animals the family prefers to foster",
    )


class FosterProfileResponse(BaseModel):
    """Foster profile details."""

    id: UUID
    user_id: UUID
    motivation: str
    experience_description: str | None
    home_type: str
    has_outdoor_space: bool
    has_other_pets: bool
    other_pets_description: str | None
    max_animals: int
    preferred_animal_types: list[str]
    status: str
    rejection_reason: str | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    def model_post_init(self, __context: object) -> None:
        # Ensure preferred_animal_types is always a list even when stored as None
        if self.preferred_animal_types is None:  # type: ignore[comparison-overlap]
            object.__setattr__(self, "preferred_animal_types", [])


class FosterListResponse(BaseModel):
    """Paginated list of foster profiles."""

    items: list[FosterProfileResponse]
    total: int
    page: int
    page_size: int


class FosterReviewRequest(BaseModel):
    """Staff payload for approving or rejecting a foster application."""

    approved: bool = Field(
        ...,
        description="True to approve, False to reject",
    )
    rejection_reason: str | None = Field(
        None,
        max_length=1000,
        description="Required when rejecting; optional when approving",
    )


class FosterHomeTypesResponse(BaseModel):
    """Available home type options."""

    home_types: list[str]


class FosterAnimalTypesResponse(BaseModel):
    """Available animal type preference options."""

    animal_types: list[str]


# ---------------------------------------------------------------------------
# Endpoints — Public (authenticated)
# ---------------------------------------------------------------------------


@public_router.get(
    "/api/foster/home-types",
    response_model=FosterHomeTypesResponse,
)
async def list_foster_home_types() -> FosterHomeTypesResponse:
    """Return all valid home type values for foster applications."""
    return FosterHomeTypesResponse(home_types=sorted(h.value for h in HomeType))


@public_router.get(
    "/api/foster/animal-types",
    response_model=FosterAnimalTypesResponse,
)
async def list_foster_animal_types() -> FosterAnimalTypesResponse:
    """Return all valid preferred animal type values for foster applications."""
    return FosterAnimalTypesResponse(animal_types=sorted(ANIMAL_TYPE_PREFERENCE_VALUES))


@public_router.post(
    "/api/foster/apply",
    response_model=FosterProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply_as_foster(
    body: FosterApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FosterProfileResponse:
    """Submit a foster family application.

    Any authenticated user can apply. A user can only have one active profile.
    Returns 409 if the user has already applied.
    """
    existing = await db.execute(
        select(FosterProfile).where(FosterProfile.user_id == current_user.id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A foster application already exists for this account. "
            "Contact shelter staff to modify your application.",
        )

    profile = FosterProfile(
        user_id=current_user.id,
        motivation=body.motivation,
        experience_description=body.experience_description,
        home_type=body.home_type.value,
        has_outdoor_space=body.has_outdoor_space,
        has_other_pets=body.has_other_pets,
        other_pets_description=body.other_pets_description,
        max_animals=body.max_animals,
        preferred_animal_types=[t.value for t in body.preferred_animal_types],
        status=FosterStatus.PENDING.value,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    logger.info(
        "Foster application submitted",
        extra={"foster_profile_id": str(profile.id), "user_id": str(current_user.id)},
    )
    return _to_response(profile)


@public_router.get(
    "/api/foster/me",
    response_model=FosterProfileResponse,
)
async def get_my_foster_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FosterProfileResponse:
    """Get the authenticated user's own foster profile.

    Returns 404 if the user has not yet submitted an application.
    """
    result = await db.execute(select(FosterProfile).where(FosterProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No foster application found for this account.",
        )
    return _to_response(profile)


# ---------------------------------------------------------------------------
# Endpoints — Staff only
# ---------------------------------------------------------------------------


@staff_router.get(
    "/api/staff/foster",
    response_model=FosterListResponse,
)
async def list_foster_applications(
    foster_status: FosterStatus | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> FosterListResponse:
    """List all foster applications with optional status filter. Staff only."""
    count_stmt = select(func.count()).select_from(FosterProfile)
    if foster_status is not None:
        count_stmt = count_stmt.where(FosterProfile.status == foster_status.value)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    stmt = select(FosterProfile).order_by(FosterProfile.created_at.desc())
    if foster_status is not None:
        stmt = stmt.where(FosterProfile.status == foster_status.value)
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    profiles = result.scalars().all()

    return FosterListResponse(
        items=[_to_response(p) for p in profiles],
        total=total,
        page=page,
        page_size=page_size,
    )


@staff_router.get(
    "/api/staff/foster/{profile_id}",
    response_model=FosterProfileResponse,
)
async def get_foster_application(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> FosterProfileResponse:
    """Get a single foster application by ID. Staff only."""
    result = await db.execute(select(FosterProfile).where(FosterProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Foster profile {profile_id} not found.",
        )
    return _to_response(profile)


@staff_router.put(
    "/api/staff/foster/{profile_id}/review",
    response_model=FosterProfileResponse,
)
async def review_foster_application(
    profile_id: UUID,
    body: FosterReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: User = Depends(require_staff),
) -> FosterProfileResponse:
    """Approve or reject a foster application. Staff only.

    - Approved applications set status = 'approved'.
    - Rejected applications require rejection_reason and set status = 'rejected'.
    - Returns 400 if rejecting without providing a reason.
    - Returns 422 if the application is not in 'pending' status.
    """
    result = await db.execute(select(FosterProfile).where(FosterProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Foster profile {profile_id} not found.",
        )

    if profile.status != FosterStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot review a foster application with status '{profile.status}'. "
            "Only pending applications can be reviewed.",
        )

    if not body.approved and not body.rejection_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A rejection reason is required when rejecting a foster application.",
        )

    profile.status = FosterStatus.APPROVED.value if body.approved else FosterStatus.REJECTED.value
    profile.rejection_reason = body.rejection_reason if not body.approved else None
    profile.reviewed_by = current_staff.id
    profile.reviewed_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(profile)
    action = "approved" if body.approved else "rejected"
    logger.info(
        "Foster application %s",
        action,
        extra={
            "foster_profile_id": str(profile_id),
            "staff_id": str(current_staff.id),
            "action": action,
        },
    )
    return _to_response(profile)


# ---------------------------------------------------------------------------
# Endpoints — Placement matching (staff only, RAP-191)
# ---------------------------------------------------------------------------


@staff_router.get(
    "/api/staff/foster/match/{animal_id}",
    summary="Find best foster families for an animal",
)
async def match_foster_for_animal(
    animal_id: UUID,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Return approved foster families ranked by compatibility with the given animal.

    Families at maximum capacity are excluded.  The response includes a
    match_score (0-100), human-readable why_match and why_not lists, and
    remaining capacity for each family.

    Staff only.
    """
    return await find_foster_matches_for_animal(db, animal_id, limit=limit, offset=offset)


@staff_router.get(
    "/api/staff/foster/{profile_id}/matches",
    summary="Find best animals for a foster family",
)
async def match_animals_for_foster(
    profile_id: UUID,
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Return fosterable animals ranked by compatibility with the given foster family.

    Only animals with fosterable statuses (intake, quarantine, available,
    under_treatment) are considered.  Returns an empty list if the family is
    at capacity or not in approved status.

    Staff only.
    """
    return await find_animal_matches_for_foster(db, profile_id, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# Check-in Schemas (RAP-192)
# ---------------------------------------------------------------------------


class CheckInResponse(BaseModel):
    """Foster check-in record."""

    id: UUID
    foster_placement_id: UUID
    check_in_type: str
    status: str
    scheduled_at: datetime
    completed_at: datetime | None
    notes: str | None
    cancellation_reason: str | None
    interval_days: int
    reminder_sent_at: datetime | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CheckInListResponse(BaseModel):
    """Paginated list of check-ins."""

    items: list[CheckInResponse]
    total: int
    page: int
    page_size: int


class CreateCheckInRequest(BaseModel):
    """Staff payload to schedule a check-in."""

    scheduled_at: datetime = Field(
        ...,
        description="When the check-in should occur (ISO 8601 datetime with timezone)",
    )
    check_in_type: CheckInType = Field(
        default=CheckInType.SCHEDULED,
        description="Whether this is a routine scheduled or unscheduled check-in",
    )
    interval_days: int = Field(
        default=DEFAULT_INTERVAL_DAYS,
        ge=MIN_INTERVAL_DAYS,
        le=MAX_INTERVAL_DAYS,
        description="Days until the next check-in should be auto-scheduled after completion",
    )


class CompleteCheckInRequest(BaseModel):
    """Staff payload to mark a check-in as completed."""

    notes: str | None = Field(
        None,
        max_length=CHECK_IN_NOTES_MAX_LENGTH,
        description="Staff notes from the check-in call or visit",
    )
    auto_schedule_next: bool = Field(
        default=True,
        description="Automatically schedule the next check-in based on interval_days",
    )


class CancelCheckInRequest(BaseModel):
    """Staff payload to cancel a pending check-in."""

    reason: str | None = Field(
        None,
        max_length=500,
        description="Optional cancellation reason",
    )


# ---------------------------------------------------------------------------
# Endpoints — Check-in schedule (staff only, RAP-192)
# ---------------------------------------------------------------------------


@staff_router.post(
    "/api/staff/foster/placements/{placement_id}/check-ins",
    response_model=CheckInResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a foster check-in",
)
async def schedule_foster_check_in(
    placement_id: UUID,
    body: CreateCheckInRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: User = Depends(require_staff),
) -> CheckInResponse:
    """Schedule a welfare check-in for an active foster placement.

    Returns 404 if the placement is not found or has already ended.
    Staff only.
    """
    try:
        check_in = await create_check_in(
            db,
            placement_id=placement_id,
            scheduled_at=body.scheduled_at,
            check_in_type=body.check_in_type,
            interval_days=body.interval_days,
            created_by=current_staff.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_check_in_response(check_in)


@staff_router.get(
    "/api/staff/foster/placements/{placement_id}/check-ins",
    response_model=CheckInListResponse,
    summary="List check-ins for a foster placement",
)
async def list_placement_check_ins(
    placement_id: UUID,
    check_in_status: CheckInStatus | None = Query(
        None, alias="status", description="Filter by status"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> CheckInListResponse:
    """Return paginated check-ins for a specific foster placement. Staff only."""
    items, total = await list_check_ins_for_placement(
        db,
        placement_id,
        status_filter=check_in_status,
        page=page,
        page_size=page_size,
    )
    return CheckInListResponse(
        items=[_to_check_in_response(ci) for ci in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@staff_router.get(
    "/api/staff/foster/check-ins/upcoming",
    response_model=CheckInListResponse,
    summary="List upcoming and overdue foster check-ins",
)
async def list_upcoming_foster_check_ins(
    days_ahead: int = Query(
        UPCOMING_WINDOW_DAYS, ge=1, le=90, description="Look-ahead window in days"
    ),
    include_overdue: bool = Query(True, description="Include overdue (past-due) pending check-ins"),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> CheckInListResponse:
    """Return pending check-ins due within `days_ahead` days (and overdue ones if requested).

    Useful for a staff dashboard showing what check-ins are coming up or missed.
    Staff only.
    """
    items, total = await list_upcoming_check_ins(
        db,
        days_ahead=days_ahead,
        include_overdue=include_overdue,
        page=page,
        page_size=page_size,
    )
    return CheckInListResponse(
        items=[_to_check_in_response(ci) for ci in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@staff_router.put(
    "/api/staff/foster/check-ins/{check_in_id}/complete",
    response_model=CheckInResponse,
    summary="Complete a foster check-in",
)
async def complete_foster_check_in(
    check_in_id: UUID,
    body: CompleteCheckInRequest,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> CheckInResponse:
    """Mark a pending check-in as completed with optional staff notes.

    If auto_schedule_next is True, automatically creates the next check-in
    based on the interval_days stored on this check-in.

    Returns 404 if not found.
    Returns 422 if the check-in is not in pending status.
    Staff only.
    """
    try:
        check_in = await complete_check_in(
            db,
            check_in_id,
            notes=body.notes,
            auto_schedule_next=body.auto_schedule_next,
        )
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg) from exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error_msg
        ) from exc
    return _to_check_in_response(check_in)


@staff_router.put(
    "/api/staff/foster/check-ins/{check_in_id}/cancel",
    response_model=CheckInResponse,
    summary="Cancel a foster check-in",
)
async def cancel_foster_check_in(
    check_in_id: UUID,
    body: CancelCheckInRequest,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> CheckInResponse:
    """Cancel a pending check-in.

    Returns 404 if not found.
    Returns 422 if the check-in is not in pending status.
    Staff only.
    """
    try:
        check_in = await cancel_check_in(db, check_in_id, reason=body.reason)
    except ValueError as exc:
        error_msg = str(exc)
        if "not found" in error_msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_msg) from exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error_msg
        ) from exc
    return _to_check_in_response(check_in)


@staff_router.post(
    "/api/staff/foster/check-ins/{check_in_id}/remind",
    response_model=CheckInResponse,
    summary="Log reminder dispatch for a foster check-in",
)
async def send_foster_check_in_reminder(
    check_in_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> CheckInResponse:
    """Record that a reminder was dispatched for this check-in.

    Updates reminder_sent_at timestamp.  Actual notification delivery is
    handled by the notification service layer and is outside this endpoint's
    scope.

    Returns 404 if not found.
    Staff only.
    """
    try:
        check_in = await record_reminder_sent(db, check_in_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_check_in_response(check_in)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_check_in_response(check_in: FosterCheckIn) -> CheckInResponse:
    """Convert ORM FosterCheckIn to CheckInResponse schema."""
    return CheckInResponse(
        id=check_in.id,
        foster_placement_id=check_in.foster_placement_id,
        check_in_type=check_in.check_in_type,
        status=check_in.status,
        scheduled_at=check_in.scheduled_at,
        completed_at=check_in.completed_at,
        notes=check_in.notes,
        cancellation_reason=check_in.cancellation_reason,
        interval_days=check_in.interval_days,
        reminder_sent_at=check_in.reminder_sent_at,
        created_by=check_in.created_by,
        created_at=check_in.created_at,
        updated_at=check_in.updated_at,
    )


def _to_response(profile: FosterProfile) -> FosterProfileResponse:
    """Convert ORM object to response schema, normalising JSON list fields."""
    return FosterProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        motivation=profile.motivation,
        experience_description=profile.experience_description,
        home_type=profile.home_type,
        has_outdoor_space=profile.has_outdoor_space,
        has_other_pets=profile.has_other_pets,
        other_pets_description=profile.other_pets_description,
        max_animals=profile.max_animals,
        preferred_animal_types=profile.preferred_animal_types or [],
        status=profile.status,
        rejection_reason=profile.rejection_reason,
        reviewed_by=profile.reviewed_by,
        reviewed_at=profile.reviewed_at,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )
