"""Rescuer profile endpoints — registration, public lookup, and profile update.

Endpoints:
  POST /api/rescuers/register       -- register as a rescuer (authenticated)
  GET  /api/rescuers/{slug}          -- public profile lookup
  PUT  /api/rescuers/profile         -- update own profile (authenticated)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user
from src.db.models.user import User
from src.db.session import get_db
from src.services.rescuer_profile_service import (
    RescuerProfileError,
    RescuerProfileExistsError,
    RescuerProfileNotFoundError,
    get_rescuer_by_slug,
    register_rescuer,
    update_rescuer_profile,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/rescuers",
    tags=["rescuer-profiles"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RescuerRegisterRequest(BaseModel):
    """Request body for rescuer registration."""

    display_name: str = Field(..., min_length=2, max_length=100, description="Public display name")
    bio: str | None = Field(default=None, max_length=1000, description="Bio/description")
    location_city: str | None = Field(default=None, max_length=100, description="City name")
    location_coords: dict | None = Field(default=None, description="Coordinates {lat, lng}")
    social_links: dict | None = Field(
        default=None,
        description="Social links {facebook, instagram, whatsapp, email}",
    )
    phone_whatsapp: str | None = Field(
        default=None, max_length=20, description="WhatsApp phone (+595...)"
    )


class RescuerProfileResponse(BaseModel):
    """Response schema for a rescuer profile."""

    id: UUID
    user_id: UUID
    display_name: str
    slug: str
    bio: str | None
    location_city: str | None
    location_coords: dict | None
    social_links: dict | None
    phone_whatsapp: str | None
    is_verified: bool
    verification_method: str | None
    animal_count: int
    supporter_count: int

    model_config = {"from_attributes": True}


class RescuerUpdateRequest(BaseModel):
    """Request body for profile update. All fields optional."""

    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    bio: str | None = Field(default=None, max_length=1000)
    location_city: str | None = Field(default=None, max_length=100)
    location_coords: dict | None = None
    social_links: dict | None = None
    phone_whatsapp: str | None = Field(default=None, max_length=20)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=RescuerProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register as a rescuer",
    description="Create a rescuer profile for the authenticated user.",
)
async def register_rescuer_endpoint(
    body: RescuerRegisterRequest,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RescuerProfileResponse:
    """Register a new rescuer profile."""
    try:
        profile = await register_rescuer(
            user_id=current_user.id,
            display_name=body.display_name,
            bio=body.bio,
            location_city=body.location_city,
            location_coords=body.location_coords,
            social_links=body.social_links,
            phone_whatsapp=body.phone_whatsapp,
            db=db,
        )
    except RescuerProfileExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "conflict",
                "message": "You already have a rescuer profile",
            },
        ) from None
    except RescuerProfileError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": exc.message,
                "details": exc.details,
            },
        ) from None

    await db.commit()
    return RescuerProfileResponse.model_validate(profile)


@router.get(
    "/{slug}",
    response_model=RescuerProfileResponse,
    summary="Get rescuer public profile",
    description="Look up a rescuer profile by slug (public, no auth required).",
)
async def get_rescuer_profile(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> RescuerProfileResponse:
    """Get a rescuer profile by slug."""
    try:
        profile = await get_rescuer_by_slug(slug, db)
    except RescuerProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Rescuer profile not found"},
        ) from None

    return RescuerProfileResponse.model_validate(profile)


@router.put(
    "/profile",
    response_model=RescuerProfileResponse,
    summary="Update rescuer profile",
    description="Update the authenticated user's rescuer profile.",
)
async def update_rescuer_profile_endpoint(
    body: RescuerUpdateRequest,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RescuerProfileResponse:
    """Update the current user's rescuer profile."""
    # Build kwargs, using sentinel ... for "not provided"
    kwargs: dict = {"user_id": current_user.id, "db": db}
    if body.display_name is not None:
        kwargs["display_name"] = body.display_name
    if body.bio is not None:
        kwargs["bio"] = body.bio
    if body.location_city is not None:
        kwargs["location_city"] = body.location_city
    if body.location_coords is not None:
        kwargs["location_coords"] = body.location_coords
    if body.social_links is not None:
        kwargs["social_links"] = body.social_links
    if body.phone_whatsapp is not None:
        kwargs["phone_whatsapp"] = body.phone_whatsapp

    try:
        profile = await update_rescuer_profile(**kwargs)
    except RescuerProfileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": "You don't have a rescuer profile. Register first.",
            },
        ) from None
    except RescuerProfileError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": exc.message,
                "details": exc.details,
            },
        ) from None

    await db.commit()
    return RescuerProfileResponse.model_validate(profile)
