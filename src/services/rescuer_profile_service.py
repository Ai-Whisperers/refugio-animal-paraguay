"""Rescuer profile service — registration, lookup, and profile management.

Handles rescuer self-registration with slug generation, profile updates,
and public profile lookups.
"""

import logging
import re
import unicodedata
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.rescuer_profile import RescuerProfile

logger = logging.getLogger(__name__)

# Display name constraints
MIN_DISPLAY_NAME_LENGTH = 2
MAX_DISPLAY_NAME_LENGTH = 100
MAX_BIO_LENGTH = 1000

# Paraguay phone format
PARAGUAY_PHONE_PATTERN = re.compile(r"^\+595\d{8,10}$")

# Slug generation
MAX_SLUG_LENGTH = 120
SLUG_SUFFIX_SEPARATOR = "-"


class RescuerProfileError(Exception):
    """Base error for rescuer profile operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class RescuerProfileExistsError(RescuerProfileError):
    """Raised when a user already has a rescuer profile."""

    def __init__(self, user_id: UUID) -> None:
        super().__init__(
            message="Rescuer profile already exists",
            details=f"User {user_id} already has a rescuer profile",
        )
        self.user_id = user_id


class DisplayNameTakenError(RescuerProfileError):
    """Raised when a display name generates a duplicate slug."""

    def __init__(self, display_name: str) -> None:
        super().__init__(
            message="Display name already taken",
            details=f"A profile with a similar name to '{display_name}' already exists",
        )
        self.display_name = display_name


class RescuerProfileNotFoundError(RescuerProfileError):
    """Raised when a rescuer profile is not found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(
            message="Rescuer profile not found",
            details=f"No profile found for: {identifier}",
        )
        self.identifier = identifier


def generate_slug(display_name: str) -> str:
    """Generate a URL-friendly slug from a display name.

    Normalizes unicode, strips accents, lowercases, and replaces
    non-alphanumeric characters with hyphens.
    """
    # Normalize unicode and strip accents
    normalized = unicodedata.normalize("NFKD", display_name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    # Lowercase and replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower())

    # Strip leading/trailing hyphens
    slug = slug.strip("-")

    # Truncate to max length
    if len(slug) > MAX_SLUG_LENGTH:
        slug = slug[:MAX_SLUG_LENGTH].rstrip("-")

    return slug or "rescuer"


def validate_display_name(display_name: str) -> None:
    """Validate display name length."""
    if len(display_name) < MIN_DISPLAY_NAME_LENGTH:
        raise RescuerProfileError(
            message="Display name too short",
            details=f"Minimum {MIN_DISPLAY_NAME_LENGTH} characters required",
        )
    if len(display_name) > MAX_DISPLAY_NAME_LENGTH:
        raise RescuerProfileError(
            message="Display name too long",
            details=f"Maximum {MAX_DISPLAY_NAME_LENGTH} characters allowed",
        )


def validate_bio(bio: str | None) -> None:
    """Validate bio length."""
    if bio and len(bio) > MAX_BIO_LENGTH:
        raise RescuerProfileError(
            message="Bio too long",
            details=f"Maximum {MAX_BIO_LENGTH} characters allowed",
        )


def validate_phone(phone: str | None) -> None:
    """Validate Paraguay phone format (+595XXXXXXXXX)."""
    if phone and not PARAGUAY_PHONE_PATTERN.match(phone):
        raise RescuerProfileError(
            message="Invalid phone format",
            details="Phone must be in format +595XXXXXXXXX",
        )


def validate_contact_method(phone: str | None, social_links: dict | None) -> None:
    """Ensure at least one contact method is provided."""
    has_phone = bool(phone)
    has_social = bool(social_links) and any(social_links.values())
    if not has_phone and not has_social:
        raise RescuerProfileError(
            message="Contact method required",
            details="At least one contact method (phone or social link) is required",
        )


async def _ensure_unique_slug(db: AsyncSession, base_slug: str) -> str:
    """Generate a unique slug, appending a number if needed."""
    slug = base_slug
    counter = 1

    while True:
        result = await db.execute(select(RescuerProfile.id).where(RescuerProfile.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base_slug}{SLUG_SUFFIX_SEPARATOR}{counter}"
        counter += 1
        if counter > 100:
            # Safety valve — should never happen in practice
            raise RescuerProfileError(
                message="Could not generate unique slug",
                details=f"Too many profiles with similar name to '{base_slug}'",
            )


async def register_rescuer(
    *,
    user_id: UUID,
    display_name: str,
    bio: str | None = None,
    location_city: str | None = None,
    location_coords: dict | None = None,
    social_links: dict | None = None,
    phone_whatsapp: str | None = None,
    db: AsyncSession,
) -> RescuerProfile:
    """Register a new rescuer profile.

    Raises:
        RescuerProfileExistsError: If user already has a profile.
        RescuerProfileError: If validation fails.
    """
    # Check user doesn't already have a profile
    existing = await db.execute(select(RescuerProfile.id).where(RescuerProfile.user_id == user_id))
    if existing.scalar_one_or_none() is not None:
        raise RescuerProfileExistsError(user_id)

    # Validate inputs
    validate_display_name(display_name)
    validate_bio(bio)
    validate_phone(phone_whatsapp)
    validate_contact_method(phone_whatsapp, social_links)

    # Generate unique slug
    base_slug = generate_slug(display_name)
    slug = await _ensure_unique_slug(db, base_slug)

    profile = RescuerProfile(
        user_id=user_id,
        display_name=display_name,
        slug=slug,
        bio=bio,
        location_city=location_city,
        location_coords=location_coords,
        social_links=social_links,
        phone_whatsapp=phone_whatsapp,
    )

    db.add(profile)
    await db.flush()

    logger.info(
        "Rescuer profile created: user=%s slug=%s",
        user_id,
        slug,
    )
    return profile


async def get_rescuer_by_slug(slug: str, db: AsyncSession) -> RescuerProfile:
    """Look up a rescuer profile by slug.

    Raises:
        RescuerProfileNotFoundError: If no profile found.
    """
    result = await db.execute(select(RescuerProfile).where(RescuerProfile.slug == slug))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise RescuerProfileNotFoundError(slug)
    return profile


async def update_rescuer_profile(
    *,
    user_id: UUID,
    display_name: str | None = None,
    bio: str | None = ...,  # type: ignore[assignment]
    location_city: str | None = ...,  # type: ignore[assignment]
    location_coords: dict | None = ...,  # type: ignore[assignment]
    social_links: dict | None = ...,  # type: ignore[assignment]
    phone_whatsapp: str | None = ...,  # type: ignore[assignment]
    db: AsyncSession,
) -> RescuerProfile:
    """Update an existing rescuer profile.

    Uses sentinel ... to distinguish "not provided" from None.

    Raises:
        RescuerProfileNotFoundError: If user has no profile.
        RescuerProfileError: If validation fails.
    """
    result = await db.execute(select(RescuerProfile).where(RescuerProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise RescuerProfileNotFoundError(str(user_id))

    # Update display name and regenerate slug if changed
    if display_name is not None and display_name != profile.display_name:
        validate_display_name(display_name)
        base_slug = generate_slug(display_name)
        new_slug = await _ensure_unique_slug(db, base_slug)
        profile.display_name = display_name
        profile.slug = new_slug

    if bio is not ...:
        validate_bio(bio)
        profile.bio = bio

    if location_city is not ...:
        profile.location_city = location_city

    if location_coords is not ...:
        profile.location_coords = location_coords

    if social_links is not ...:
        profile.social_links = social_links

    if phone_whatsapp is not ...:
        validate_phone(phone_whatsapp)
        profile.phone_whatsapp = phone_whatsapp

    await db.flush()

    logger.info("Rescuer profile updated: user=%s slug=%s", user_id, profile.slug)
    return profile
