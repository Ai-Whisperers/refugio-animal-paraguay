"""Volunteer registration and profile API (RAP-640, RAP-641, RAP-642).

Public endpoint for volunteers to apply and view their profile.
Staff endpoint to list and review volunteer applications.
Onboarding checklist endpoints for staff + volunteers (RAP-642).

Endpoints:
    POST /api/volunteers/apply               -- submit volunteer application
    GET  /api/volunteers/me                  -- get own volunteer profile
    PUT  /api/volunteers/me                  -- update own volunteer profile (pending/inactive only)
    PUT  /api/volunteers/profile             -- update skills/availability/bio (any active volunteer)
    GET  /api/volunteers/profile/options     -- get available skill and availability options
    GET  /api/volunteers/onboarding          -- get own onboarding checklist
    GET  /api/staff/volunteers               -- list all applications (staff only)
    PUT  /api/staff/volunteers/{id}/review   -- approve/reject application (staff only)
    GET  /api/staff/volunteers/{id}          -- get a volunteer profile by ID (staff only)
    POST /api/staff/volunteers/{id}/onboarding       -- initialize onboarding checklist
    PUT  /api/staff/volunteers/{id}/onboarding/{key} -- mark checklist item complete/incomplete
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user as get_current_user
from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.models.volunteer_onboarding import (
    MANDATORY_ITEM_KEYS,
    ONBOARDING_ITEMS,
    VolunteerOnboardingItem,
)
from src.db.models.volunteer_profile import (
    VOLUNTEER_SKILL_OPTIONS,
    VolunteerAvailability,
    VolunteerProfile,
    VolunteerStatus,
)
from src.db.session import get_db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class VolunteerApplyRequest(BaseModel):
    """Payload for submitting a volunteer application."""

    motivation: str = Field(
        ...,
        min_length=20,
        max_length=2000,
        description="Why the applicant wants to volunteer",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Skills the volunteer brings",
    )
    availability: list[str] = Field(
        default_factory=list,
        description="When the volunteer is available",
    )
    hours_per_week: int | None = Field(
        None,
        ge=1,
        le=40,
        description="Estimated hours per week available",
    )
    emergency_contact_name: str | None = Field(
        None,
        max_length=100,
        description="Emergency contact full name",
    )
    emergency_contact_phone: str | None = Field(
        None,
        max_length=20,
        description="Emergency contact phone number",
    )


class VolunteerProfileResponse(BaseModel):
    """Volunteer profile details."""

    id: UUID
    user_id: UUID
    full_name: str | None
    email: str
    motivation: str
    bio: str | None
    skills: list[str]
    availability: list[str]
    hours_per_week: int | None
    languages_spoken: list[str]
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    status: str
    rejection_reason: str | None
    total_hours_logged: float
    created_at: datetime

    model_config = {"from_attributes": True}


class VolunteerProfileUpdateRequest(BaseModel):
    """Payload for updating skills, availability, and bio (available for approved volunteers)."""

    bio: str | None = Field(None, max_length=500, description="Short volunteer bio")
    skills: list[str] | None = Field(None, description="Skill tags from available options")
    availability: list[str] | None = Field(None, description="Availability windows")
    hours_per_week: int | None = Field(None, ge=1, le=40, description="Estimated hours per week")
    languages_spoken: list[str] | None = Field(None, description="Languages spoken by volunteer")


class VolunteerProfileOptions(BaseModel):
    """Available options for skills and availability selection."""

    skills: list[str]
    availability: list[str]


class VolunteerUpdateRequest(BaseModel):
    """Payload for updating own volunteer profile (pre-approval)."""

    motivation: str | None = Field(None, min_length=20, max_length=2000)
    skills: list[str] | None = None
    availability: list[str] | None = None
    hours_per_week: int | None = Field(None, ge=1, le=40)
    emergency_contact_name: str | None = Field(None, max_length=100)
    emergency_contact_phone: str | None = Field(None, max_length=20)


class VolunteerReviewRequest(BaseModel):
    """Staff review payload for approving or rejecting a volunteer application."""

    decision: VolunteerStatus = Field(
        ...,
        description="Approval decision: 'approved' or 'rejected'",
    )
    rejection_reason: str | None = Field(
        None,
        max_length=500,
        description="Required when decision is 'rejected'",
    )


class VolunteerListItem(BaseModel):
    """Summary row for staff volunteer list."""

    id: UUID
    user_id: UUID
    full_name: str | None
    email: str
    status: str
    skills: list[str]
    hours_per_week: int | None
    created_at: datetime


class PaginatedVolunteerList(BaseModel):
    """Paginated list of volunteer applications."""

    items: list[VolunteerListItem]
    total: int
    page: int
    page_size: int


class OnboardingItemResponse(BaseModel):
    """Single onboarding checklist item."""

    id: UUID
    item_key: str
    title: str
    is_mandatory: bool
    completed: bool
    completed_at: datetime | None
    notes: str | None

    model_config = {"from_attributes": True}


class OnboardingChecklistResponse(BaseModel):
    """Full onboarding checklist for a volunteer."""

    items: list[OnboardingItemResponse]
    total: int
    completed_count: int
    mandatory_complete: bool


class OnboardingItemUpdateRequest(BaseModel):
    """Staff payload for marking an onboarding item complete or incomplete."""

    completed: bool = Field(..., description="True to mark complete, False to revert")
    notes: str | None = Field(None, max_length=500, description="Optional notes from staff")


# ---------------------------------------------------------------------------
# Public router
# ---------------------------------------------------------------------------

public_router = APIRouter(prefix="/api/volunteers", tags=["volunteers"])


@public_router.post(
    "/apply",
    response_model=VolunteerProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a volunteer application",
)
async def apply_as_volunteer(
    payload: VolunteerApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Submit a volunteer application for the current user.

    The user must be authenticated. If they already have a profile, this
    returns their existing profile (idempotent for pending applications).
    """
    # Check for duplicate application
    result = await db.execute(
        select(VolunteerProfile).where(VolunteerProfile.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        if existing.status in (VolunteerStatus.PENDING, VolunteerStatus.APPROVED):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You already have a volunteer profile with status '{existing.status}'",
            )
        # Allow re-application if rejected or inactive
        existing.motivation = payload.motivation
        existing.skills = payload.skills or []
        existing.availability = payload.availability or []
        existing.hours_per_week = payload.hours_per_week
        existing.emergency_contact_name = payload.emergency_contact_name
        existing.emergency_contact_phone = payload.emergency_contact_phone
        existing.status = VolunteerStatus.PENDING
        existing.rejection_reason = None
        existing.reviewed_by = None
        existing.reviewed_at = None
        await db.flush()
        await db.refresh(existing)
        profile = existing
    else:
        profile = VolunteerProfile(
            user_id=current_user.id,
            motivation=payload.motivation,
            skills=payload.skills or [],
            availability=payload.availability or [],
            hours_per_week=payload.hours_per_week,
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
            status=VolunteerStatus.PENDING,
        )
        db.add(profile)
        await db.flush()
        await db.refresh(profile)

    logger.info("Volunteer application submitted: user_id=%s", str(current_user.id)[:8] + "...")
    return _build_profile_response(profile, current_user)


@public_router.get(
    "/me",
    response_model=VolunteerProfileResponse,
    summary="Get own volunteer profile",
)
async def get_my_volunteer_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return the current user's volunteer profile."""
    result = await db.execute(
        select(VolunteerProfile).where(VolunteerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No volunteer profile found. Submit an application first.",
        )
    return _build_profile_response(profile, current_user)


@public_router.put(
    "/me",
    response_model=VolunteerProfileResponse,
    summary="Update own volunteer profile",
)
async def update_my_volunteer_profile(
    payload: VolunteerUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update the current user's volunteer profile.

    Only allowed when the profile is in 'pending' or 'inactive' state.
    Approved volunteers must contact staff to modify their profile.
    """
    result = await db.execute(
        select(VolunteerProfile).where(VolunteerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No volunteer profile found.",
        )
    if profile.status == VolunteerStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approved volunteer profiles can only be modified by staff.",
        )

    if payload.motivation is not None:
        profile.motivation = payload.motivation
    if payload.skills is not None:
        profile.skills = payload.skills
    if payload.availability is not None:
        profile.availability = payload.availability
    if payload.hours_per_week is not None:
        profile.hours_per_week = payload.hours_per_week
    if payload.emergency_contact_name is not None:
        profile.emergency_contact_name = payload.emergency_contact_name
    if payload.emergency_contact_phone is not None:
        profile.emergency_contact_phone = payload.emergency_contact_phone

    await db.flush()
    await db.refresh(profile)
    logger.info("Volunteer profile updated: user_id=%s", str(current_user.id)[:8] + "...")
    return _build_profile_response(profile, current_user)


@public_router.put(
    "/profile",
    response_model=VolunteerProfileResponse,
    summary="Update volunteer skills, availability and bio",
)
async def update_volunteer_profile(
    payload: VolunteerProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update volunteer skills, availability, bio and languages.

    Available to volunteers in any non-rejected status (pending, approved, inactive).
    Unlike PUT /me, this endpoint allows approved volunteers to update their own profile
    for the fields that don't require staff involvement.
    """
    result = await db.execute(
        select(VolunteerProfile).where(VolunteerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No volunteer profile found. Submit an application first.",
        )
    if profile.status == VolunteerStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rejected volunteer profiles cannot be updated. Submit a new application.",
        )

    if payload.bio is not None:
        profile.bio = payload.bio
    if payload.skills is not None:
        profile.skills = payload.skills
    if payload.availability is not None:
        profile.availability = payload.availability
    if payload.hours_per_week is not None:
        profile.hours_per_week = payload.hours_per_week
    if payload.languages_spoken is not None:
        profile.languages_spoken = payload.languages_spoken

    await db.flush()
    await db.refresh(profile)
    logger.info(
        "Volunteer profile (skills/availability) updated: user_id=%s",
        str(current_user.id)[:8] + "...",
    )
    return _build_profile_response(profile, current_user)


@public_router.get(
    "/profile/options",
    response_model=VolunteerProfileOptions,
    summary="Get available skill and availability options",
)
async def get_volunteer_profile_options() -> VolunteerProfileOptions:
    """Return the available skill tags and availability windows for profile forms."""
    return VolunteerProfileOptions(
        skills=sorted(VOLUNTEER_SKILL_OPTIONS),
        availability=[a.value for a in VolunteerAvailability],
    )


@public_router.get(
    "/onboarding",
    response_model=OnboardingChecklistResponse,
    summary="Get own onboarding checklist",
)
async def get_my_onboarding_checklist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return the current user's onboarding checklist.

    Requires the user to have an approved volunteer profile.
    Returns all checklist items with completion status.
    """
    # Verify profile exists and is approved
    profile_result = await db.execute(
        select(VolunteerProfile).where(VolunteerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No volunteer profile found.",
        )
    if profile.status != VolunteerStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Onboarding checklist is only available for approved volunteers.",
        )

    items_result = await db.execute(
        select(VolunteerOnboardingItem)
        .where(VolunteerOnboardingItem.volunteer_id == profile.id)
        .order_by(VolunteerOnboardingItem.created_at)
    )
    items = items_result.scalars().all()

    completed_count = sum(1 for it in items if it.completed)
    mandatory_complete = all(it.completed for it in items if it.is_mandatory)

    return OnboardingChecklistResponse(
        items=[
            OnboardingItemResponse(
                id=it.id,
                item_key=it.item_key,
                title=it.title,
                is_mandatory=it.is_mandatory,
                completed=it.completed,
                completed_at=it.completed_at,
                notes=it.notes,
            )
            for it in items
        ],
        total=len(items),
        completed_count=completed_count,
        mandatory_complete=mandatory_complete,
    )


# ---------------------------------------------------------------------------
# Staff router
# ---------------------------------------------------------------------------

staff_router = APIRouter(prefix="/api/staff/volunteers", tags=["volunteers-staff"])


@staff_router.get(
    "",
    response_model=PaginatedVolunteerList,
    summary="List volunteer applications (staff only)",
)
async def list_volunteer_applications(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Any:
    """Return a paginated list of volunteer applications filtered by status."""
    query = select(VolunteerProfile)
    if status_filter:
        query = query.where(VolunteerProfile.status == status_filter)
    query = query.order_by(VolunteerProfile.created_at.desc())

    # Total count
    count_query = select(func.count()).select_from(VolunteerProfile)
    if status_filter:
        count_query = count_query.where(VolunteerProfile.status == status_filter)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginated results
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    profiles = result.scalars().all()

    # Load users for each profile
    user_ids = [p.user_id for p in profiles]
    items: list[VolunteerListItem] = []

    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users_by_id = {u.id: u for u in users_result.scalars().all()}
        for profile in profiles:
            user = users_by_id.get(profile.user_id)
            items.append(
                VolunteerListItem(
                    id=profile.id,
                    user_id=profile.user_id,
                    full_name=user.full_name if user else None,
                    email=user.email if user else "",
                    status=profile.status,
                    skills=profile.skills or [],
                    hours_per_week=profile.hours_per_week,
                    created_at=profile.created_at,
                )
            )

    return PaginatedVolunteerList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@staff_router.put(
    "/{volunteer_id}/review",
    response_model=VolunteerProfileResponse,
    summary="Approve or reject a volunteer application (staff only)",
)
async def review_volunteer_application(
    volunteer_id: UUID,
    payload: VolunteerReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> Any:
    """Approve or reject a pending volunteer application."""
    result = await db.execute(select(VolunteerProfile).where(VolunteerProfile.id == volunteer_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer application not found.",
        )
    if profile.status != VolunteerStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot review an application with status '{profile.status}'.",
        )
    if payload.decision == VolunteerStatus.REJECTED and not payload.rejection_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A rejection reason is required when rejecting an application.",
        )

    profile.status = payload.decision
    profile.reviewed_by = current_user.id
    profile.reviewed_at = datetime.now(UTC)
    if payload.decision == VolunteerStatus.REJECTED:
        profile.rejection_reason = payload.rejection_reason

    await db.flush()
    await db.refresh(profile)

    # Load volunteer user for response
    user_result = await db.execute(select(User).where(User.id == profile.user_id))
    volunteer_user = user_result.scalar_one_or_none()

    logger.info(
        "Volunteer application %s %s by staff %s",
        str(volunteer_id)[:8] + "...",
        payload.decision,
        str(current_user.id)[:8] + "...",
    )
    return _build_profile_response(profile, volunteer_user)


@staff_router.get(
    "/{volunteer_id}",
    response_model=VolunteerProfileResponse,
    summary="Get a volunteer profile by ID (staff only)",
)
async def get_volunteer_profile_by_id(
    volunteer_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Any:
    """Return full volunteer profile for a given volunteer ID."""
    result = await db.execute(select(VolunteerProfile).where(VolunteerProfile.id == volunteer_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer application not found.",
        )
    user_result = await db.execute(select(User).where(User.id == profile.user_id))
    volunteer_user = user_result.scalar_one_or_none()
    return _build_profile_response(profile, volunteer_user)


@staff_router.post(
    "/{volunteer_id}/onboarding",
    response_model=OnboardingChecklistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize onboarding checklist for a volunteer (staff only)",
)
async def initialize_onboarding_checklist(
    volunteer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> Any:
    """Create the standard onboarding checklist for an approved volunteer.

    Idempotent — calling this on a volunteer that already has a checklist
    adds only missing items (does not reset existing completion state).
    Requires the volunteer to be in 'approved' status.
    """
    # Find the volunteer profile
    result = await db.execute(select(VolunteerProfile).where(VolunteerProfile.id == volunteer_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer profile not found.",
        )
    if profile.status != VolunteerStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Onboarding checklist can only be created for approved volunteers (current status: {profile.status}).",
        )

    # Get existing items to avoid duplicates (idempotent)
    existing_result = await db.execute(
        select(VolunteerOnboardingItem).where(VolunteerOnboardingItem.volunteer_id == volunteer_id)
    )
    existing_keys = {it.item_key for it in existing_result.scalars().all()}

    # Create missing items
    new_items = []
    for item_key, title in ONBOARDING_ITEMS.items():
        if item_key not in existing_keys:
            item = VolunteerOnboardingItem(
                volunteer_id=volunteer_id,
                item_key=item_key,
                title=title,
                is_mandatory=item_key in MANDATORY_ITEM_KEYS,
            )
            db.add(item)
            new_items.append(item)

    if new_items:
        await db.flush()

    # Re-fetch all items for response
    all_result = await db.execute(
        select(VolunteerOnboardingItem)
        .where(VolunteerOnboardingItem.volunteer_id == volunteer_id)
        .order_by(VolunteerOnboardingItem.created_at)
    )
    all_items = all_result.scalars().all()

    completed_count = sum(1 for it in all_items if it.completed)
    mandatory_complete = all(it.completed for it in all_items if it.is_mandatory)

    logger.info(
        "Onboarding checklist initialized for volunteer %s by staff %s (%d new items)",
        str(volunteer_id)[:8] + "...",
        str(current_user.id)[:8] + "...",
        len(new_items),
    )
    return OnboardingChecklistResponse(
        items=[
            OnboardingItemResponse(
                id=it.id,
                item_key=it.item_key,
                title=it.title,
                is_mandatory=it.is_mandatory,
                completed=it.completed,
                completed_at=it.completed_at,
                notes=it.notes,
            )
            for it in all_items
        ],
        total=len(all_items),
        completed_count=completed_count,
        mandatory_complete=mandatory_complete,
    )


@staff_router.put(
    "/{volunteer_id}/onboarding/{item_key}",
    response_model=OnboardingItemResponse,
    summary="Mark an onboarding item complete or incomplete (staff only)",
)
async def update_onboarding_item(
    volunteer_id: UUID,
    item_key: str,
    payload: OnboardingItemUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> Any:
    """Set an onboarding checklist item as complete or revert it to incomplete."""
    result = await db.execute(
        select(VolunteerOnboardingItem).where(
            VolunteerOnboardingItem.volunteer_id == volunteer_id,
            VolunteerOnboardingItem.item_key == item_key,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Onboarding item '{item_key}' not found for this volunteer.",
        )

    item.completed = payload.completed
    item.completed_at = datetime.now(UTC) if payload.completed else None
    item.completed_by = current_user.id if payload.completed else None
    if payload.notes is not None:
        item.notes = payload.notes

    await db.flush()
    await db.refresh(item)

    logger.info(
        "Onboarding item '%s' marked %s for volunteer %s by staff %s",
        item_key,
        "complete" if payload.completed else "incomplete",
        str(volunteer_id)[:8] + "...",
        str(current_user.id)[:8] + "...",
    )
    return OnboardingItemResponse(
        id=item.id,
        item_key=item.item_key,
        title=item.title,
        is_mandatory=item.is_mandatory,
        completed=item.completed,
        completed_at=item.completed_at,
        notes=item.notes,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_profile_response(profile: VolunteerProfile, user: User | None) -> dict:
    """Build the VolunteerProfileResponse dict from a profile + user."""
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": user.full_name if user else None,
        "email": user.email if user else "",
        "motivation": profile.motivation,
        "bio": profile.bio,
        "skills": profile.skills or [],
        "availability": profile.availability or [],
        "hours_per_week": profile.hours_per_week,
        "languages_spoken": profile.languages_spoken or [],
        "emergency_contact_name": profile.emergency_contact_name,
        "emergency_contact_phone": profile.emergency_contact_phone,
        "status": profile.status,
        "rejection_reason": profile.rejection_reason,
        "total_hours_logged": float(profile.total_hours_logged),
        "created_at": profile.created_at,
    }
