"""Foster family registration and approval API (RAP-190).

Any authenticated user can apply to become a foster family.
Staff can list applications and approve or reject them.

Endpoints:
    POST /api/foster/apply               -- submit foster application (authenticated)
    GET  /api/foster/me                  -- get own foster profile (authenticated)
    GET  /api/staff/foster               -- list all applications (staff only)
    PUT  /api/staff/foster/{id}/review   -- approve/reject application (staff only)
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
# Helpers
# ---------------------------------------------------------------------------


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
