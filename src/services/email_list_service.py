"""Service layer for email list management and segmentation.

Handles auto-population of email lists from existing entity types
(donors, adopters, volunteers, rescuers) and manages member lifecycle.
"""

import logging
from datetime import UTC
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.email_list import EmailList, EmailListMember, EmailListType, MemberStatus

logger = logging.getLogger(__name__)


async def populate_from_segment(
    db: AsyncSession,
    email_list: EmailList,
    overwrite: bool = False,
) -> dict[str, int]:
    """Auto-populate an email list from its segment type.

    Queries existing entities (donors, adopters, volunteers, etc.) and
    adds their emails as subscribed members. Skips emails already present
    unless overwrite=True.

    Returns:
        dict with keys 'imported', 'skipped', 'total_after'
    """
    list_type = email_list.list_type
    rows = await _fetch_segment_emails(db, list_type)

    if not rows:
        return {"imported": 0, "skipped": 0, "total_after": 0}

    existing_emails: set[str] = set()
    if not overwrite:
        result = await db.execute(
            select(EmailListMember.email).where(EmailListMember.email_list_id == email_list.id)
        )
        existing_emails = {row[0].lower() for row in result.all()}

    imported = 0
    skipped = 0

    for email, name, entity_id, source_type in rows:
        normalized = email.lower()
        if normalized in existing_emails:
            skipped += 1
            continue
        member = EmailListMember(
            email_list_id=email_list.id,
            email=normalized,
            name=name,
            status=MemberStatus.SUBSCRIBED,
            source_type=source_type,
            source_id=entity_id,
        )
        db.add(member)
        existing_emails.add(normalized)
        imported += 1

    await db.flush()

    total_result = await db.execute(
        select(EmailListMember).where(
            EmailListMember.email_list_id == email_list.id,
            EmailListMember.status == MemberStatus.SUBSCRIBED,
        )
    )
    total_after = len(total_result.scalars().all())

    logger.info(
        "Segment import complete for list %s: imported=%d skipped=%d total=%d",
        email_list.id,
        imported,
        skipped,
        total_after,
    )
    return {"imported": imported, "skipped": skipped, "total_after": total_after}


async def _fetch_segment_emails(
    db: AsyncSession,
    list_type: str,
) -> list[tuple[str, str | None, UUID | None, str]]:
    """Fetch (email, name, entity_id, source_type) tuples from the entity table."""
    if list_type == EmailListType.DONORS:
        from src.db.models.donation import Donor

        result = await db.execute(
            select(Donor.email, Donor.full_name, Donor.id).where(Donor.email.isnot(None))
        )
        return [(row[0], row[1], row[2], "donor") for row in result.all() if row[0]]

    if list_type == EmailListType.ADOPTERS:
        from src.db.models.adopter import Adopter

        result = await db.execute(
            select(Adopter.email, Adopter.full_name, Adopter.id).where(Adopter.email.isnot(None))
        )
        return [(row[0], row[1], row[2], "adopter") for row in result.all() if row[0]]

    if list_type == EmailListType.VOLUNTEERS:
        # Volunteer profiles link to users — fetch email from user table
        from src.db.models.user import User
        from src.db.models.volunteer_profile import VolunteerProfile

        result = await db.execute(
            select(User.email, User.full_name, VolunteerProfile.id).join(
                VolunteerProfile, VolunteerProfile.user_id == User.id
            )
        )
        return [(row[0], row[1], row[2], "volunteer") for row in result.all() if row[0]]

    if list_type == EmailListType.FOSTERS:
        # Foster profiles also link to users
        from src.db.models.foster_profile import FosterProfile
        from src.db.models.user import User

        result = await db.execute(
            select(User.email, User.full_name, FosterProfile.id).join(
                FosterProfile, FosterProfile.user_id == User.id
            )
        )
        return [(row[0], row[1], row[2], "foster") for row in result.all() if row[0]]

    if list_type == EmailListType.RESCUERS:
        # Rescuer profiles also link to users
        from src.db.models.rescuer_profile import RescuerProfile
        from src.db.models.user import User

        result = await db.execute(
            select(User.email, User.full_name, RescuerProfile.id).join(
                RescuerProfile, RescuerProfile.user_id == User.id
            )
        )
        return [(row[0], row[1], row[2], "rescuer") for row in result.all() if row[0]]

    return []


async def unsubscribe_by_token(
    db: AsyncSession,
    token: str,
) -> EmailListMember | None:
    """Process an unsubscribe request using the member's token.

    Returns the updated member if found, None if token is invalid.
    """
    from datetime import datetime

    result = await db.execute(
        select(EmailListMember).where(EmailListMember.unsubscribe_token == token)
    )
    member = result.scalar_one_or_none()

    if member is None:
        logger.warning("Unsubscribe token not found: %s", token[:8])
        return None

    if member.status == MemberStatus.SUBSCRIBED:
        member.status = MemberStatus.UNSUBSCRIBED
        member.unsubscribed_at = datetime.now(UTC)
        await db.flush()
        logger.info(
            "Member unsubscribed via token: list=%s email=%s",
            member.email_list_id,
            member.email,
        )

    return member
