"""Animal Update API router.

Endpoints:
  POST /animal-updates              — staff publishes a new update for an animal
  GET  /animal-updates              — paginated list of updates (staff, filter by animal_id)
  GET  /my-sponsorships/updates     — update timeline for the authenticated sponsor
  GET  /sponsorships/{id}/notification-preferences  — get sponsor notification preference
  PUT  /sponsorships/{id}/notification-preferences  — update notification preference
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user, require_staff
from src.config import Settings, get_settings
from src.db.models.animal import Animal
from src.db.models.animal_update import AnimalUpdate
from src.db.models.donation import Donor
from src.db.models.sponsorship import Sponsorship, SponsorshipStatus
from src.db.models.user import User
from src.db.session import get_db
from src.notifications.service import EmailService
from src.schemas.animal_update import (
    AnimalUpdateCreate,
    AnimalUpdateResponse,
    SponsorUpdatePreferenceResponse,
    SponsorUpdatePreferenceUpdate,
)
from src.services.sponsor_update_service import (
    get_or_create_preference,
    publish_animal_update,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["animal-updates"])


def _get_email_service(settings: Settings = Depends(get_settings)) -> EmailService:
    from src.notifications.templates import TemplateRenderer  # noqa: F401 (templates needed)

    return EmailService(settings)


# ---------------------------------------------------------------------------
# Staff endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/animal-updates",
    response_model=AnimalUpdateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish an animal update (staff)",
)
async def create_animal_update(
    body: AnimalUpdateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
    email_service: EmailService = Depends(_get_email_service),
) -> AnimalUpdateResponse:
    """Staff publishes a health, behavior, milestone, or general update for an animal.

    All active sponsors of the animal receive an email if their notification
    preference is set to immediate (the default).
    """
    # Verify animal exists
    animal_result = await db.execute(select(Animal).where(Animal.id == body.animal_id))
    animal = animal_result.scalar_one_or_none()
    if not animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal {body.animal_id} not found.",
        )

    update_record, notified = await publish_animal_update(
        db=db,
        email_service=email_service,
        animal_id=body.animal_id,
        title=body.title,
        content=body.content,
        update_type=body.update_type,
        milestone_type=body.milestone_type,
        photo_urls=body.photo_urls,
        published_by_user_id=current_user.id,
        animal_name=animal.name,
    )

    return AnimalUpdateResponse(
        id=update_record.id,
        animal_id=update_record.animal_id,
        published_by_user_id=update_record.published_by_user_id,
        title=update_record.title,
        content=update_record.content,
        update_type=update_record.update_type,
        milestone_type=update_record.milestone_type,
        photo_urls=update_record.photo_urls or [],
        published_at=update_record.published_at,
        sponsors_notified=notified,
    )


@router.get(
    "/animal-updates",
    response_model=list[AnimalUpdateResponse],
    summary="List animal updates (staff)",
)
async def list_animal_updates(
    animal_id: UUID | None = Query(default=None, description="Filter by animal"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[AnimalUpdateResponse]:
    """Paginated list of animal updates, optionally filtered by animal_id."""
    stmt = select(AnimalUpdate).order_by(AnimalUpdate.published_at.desc())
    if animal_id:
        stmt = stmt.where(AnimalUpdate.animal_id == animal_id)
    stmt = stmt.limit(limit).offset(offset)

    results = (await db.execute(stmt)).scalars().all()
    return [
        AnimalUpdateResponse(
            id=r.id,
            animal_id=r.animal_id,
            published_by_user_id=r.published_by_user_id,
            title=r.title,
            content=r.content,
            update_type=r.update_type,
            milestone_type=r.milestone_type,
            photo_urls=r.photo_urls or [],
            published_at=r.published_at,
        )
        for r in results
    ]


# ---------------------------------------------------------------------------
# Sponsor endpoints (authenticated donor user)
# ---------------------------------------------------------------------------


@router.get(
    "/my-sponsorships/updates",
    response_model=list[AnimalUpdateResponse],
    summary="Sponsor update timeline",
)
async def my_sponsorship_updates(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> list[AnimalUpdateResponse]:
    """Return the update timeline for all animals the authenticated donor sponsors.

    The donor is identified by matching their user email to a Donor record.
    """
    # Resolve donor by user email
    donor_result = await db.execute(select(Donor).where(Donor.email == current_user.email))
    donor = donor_result.scalar_one_or_none()
    if not donor:
        return []

    # Get active sponsorships for this donor
    sponsorship_result = await db.execute(
        select(Sponsorship).where(
            Sponsorship.donor_id == donor.id,
            Sponsorship.status == SponsorshipStatus.ACTIVE,
        )
    )
    sponsorships = sponsorship_result.scalars().all()
    animal_ids = [s.animal_id for s in sponsorships]
    if not animal_ids:
        return []

    stmt = (
        select(AnimalUpdate)
        .where(AnimalUpdate.animal_id.in_(animal_ids))
        .order_by(AnimalUpdate.published_at.desc())
        .limit(limit)
        .offset(offset)
    )
    updates = (await db.execute(stmt)).scalars().all()
    return [
        AnimalUpdateResponse(
            id=u.id,
            animal_id=u.animal_id,
            published_by_user_id=u.published_by_user_id,
            title=u.title,
            content=u.content,
            update_type=u.update_type,
            milestone_type=u.milestone_type,
            photo_urls=u.photo_urls or [],
            published_at=u.published_at,
        )
        for u in updates
    ]


@router.get(
    "/sponsorships/{sponsorship_id}/notification-preferences",
    response_model=SponsorUpdatePreferenceResponse,
    summary="Get sponsor notification preference",
)
async def get_notification_preference(
    sponsorship_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> SponsorUpdatePreferenceResponse:
    """Return the notification preference for a sponsorship the current user owns."""
    await _assert_sponsorship_ownership(db, sponsorship_id, current_user)
    pref = await get_or_create_preference(db, sponsorship_id)
    await db.commit()
    return SponsorUpdatePreferenceResponse.model_validate(pref)


@router.put(
    "/sponsorships/{sponsorship_id}/notification-preferences",
    response_model=SponsorUpdatePreferenceResponse,
    summary="Update sponsor notification preference",
)
async def update_notification_preference(
    sponsorship_id: UUID,
    body: SponsorUpdatePreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> SponsorUpdatePreferenceResponse:
    """Update notification preference for a sponsorship the current user owns."""
    await _assert_sponsorship_ownership(db, sponsorship_id, current_user)
    pref = await get_or_create_preference(db, sponsorship_id)
    pref.notification_enabled = body.notification_enabled
    pref.notification_frequency = body.notification_frequency
    await db.commit()
    await db.refresh(pref)
    return SponsorUpdatePreferenceResponse.model_validate(pref)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _assert_sponsorship_ownership(
    db: AsyncSession, sponsorship_id: UUID, current_user: User
) -> Sponsorship:
    """Ensure the current user owns the sponsorship. Raises 403 if not."""
    result = await db.execute(select(Sponsorship).where(Sponsorship.id == sponsorship_id))
    sponsorship = result.scalar_one_or_none()
    if not sponsorship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sponsorship {sponsorship_id} not found.",
        )

    # Verify ownership via Donor email → User email match
    donor_result = await db.execute(select(Donor).where(Donor.id == sponsorship.donor_id))
    donor = donor_result.scalar_one_or_none()
    if not donor or donor.email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this sponsorship.",
        )
    return sponsorship
