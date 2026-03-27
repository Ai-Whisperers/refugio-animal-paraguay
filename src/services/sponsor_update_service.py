"""Service for publishing animal updates and notifying sponsors via email.

When staff publishes an update:
  1. The AnimalUpdate record is persisted to the database.
  2. All active sponsorships for the animal are queried.
  3. Sponsors with notification_enabled=True and frequency=immediate
     receive an email immediately.
  4. The count of notified sponsors is returned to the caller.

Daily/weekly/monthly digest sponsors are stored but not emailed immediately —
a scheduled job (future work) handles those. For now, only immediate mode
sends emails during the publish call.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.animal_update import (
    AnimalUpdate,
    SponsorNotificationFrequency,
    SponsorUpdatePreference,
)
from src.db.models.donation import Donor
from src.db.models.sponsorship import Sponsorship, SponsorshipStatus
from src.notifications.service import EmailMessage, EmailService

logger = logging.getLogger(__name__)

# HTML email template for sponsor updates
_SPONSOR_UPDATE_TEMPLATE = """
<html>
<body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
<h2 style="color: #2e7d32;">Update about {animal_name}</h2>
<h3>{title}</h3>
<p>{content}</p>
{milestone_block}
{photos_block}
<hr/>
<p style="color: #666; font-size: 12px;">
Thank you for sponsoring {animal_name} at Refugio Animal Paraguay.<br/>
To manage your notification preferences, log in to your sponsor dashboard.
</p>
</body>
</html>
"""

_MILESTONE_BLOCK = "<p><strong>Milestone:</strong> {milestone_type}</p>"
_PHOTO_BLOCK = '<img src="{url}" style="max-width:100%;margin:8px 0;" alt="Animal photo"/>'


def _render_update_email(
    animal_name: str,
    title: str,
    content: str,
    milestone_type: str | None,
    photo_urls: list[str],
) -> str:
    """Render the HTML email body for a sponsor update."""
    milestone_block = (
        _MILESTONE_BLOCK.format(milestone_type=milestone_type.replace("_", " ").title())
        if milestone_type
        else ""
    )
    photos_block = "".join(
        _PHOTO_BLOCK.format(url=url) for url in photo_urls[:5]  # cap at 5 photos per email
    )
    return _SPONSOR_UPDATE_TEMPLATE.format(
        animal_name=animal_name,
        title=title,
        content=content,
        milestone_block=milestone_block,
        photos_block=photos_block,
    )


async def publish_animal_update(
    db: AsyncSession,
    email_service: EmailService,
    animal_id: UUID,
    title: str,
    content: str,
    update_type: str,
    milestone_type: str | None,
    photo_urls: list[str],
    published_by_user_id: UUID | None,
    animal_name: str,
) -> tuple[AnimalUpdate, int]:
    """Persist an animal update and notify immediate-mode sponsors.

    Returns (AnimalUpdate record, number of sponsors notified).
    """
    update = AnimalUpdate(
        animal_id=animal_id,
        published_by_user_id=published_by_user_id,
        title=title,
        content=content,
        update_type=update_type,
        milestone_type=milestone_type,
        photo_urls=photo_urls,
    )
    db.add(update)
    await db.flush()  # Populate update.id

    notified = 0
    if email_service.is_enabled:
        notified = await _notify_immediate_sponsors(
            db=db,
            email_service=email_service,
            animal_id=animal_id,
            animal_name=animal_name,
            update=update,
        )

    await db.commit()
    logger.info(
        "Animal update published: id=%s animal_id=%s sponsors_notified=%d",
        update.id,
        animal_id,
        notified,
    )
    return update, notified


async def _notify_immediate_sponsors(
    db: AsyncSession,
    email_service: EmailService,
    animal_id: UUID,
    animal_name: str,
    update: AnimalUpdate,
) -> int:
    """Email all sponsors of animal_id who have immediate notification enabled.

    Returns the count of emails successfully sent.
    """
    # Join Sponsorship → SponsorUpdatePreference → Donor
    # Only active sponsorships with immediate frequency and notifications enabled
    stmt = (
        select(Sponsorship, SponsorUpdatePreference, Donor)
        .join(
            SponsorUpdatePreference,
            SponsorUpdatePreference.sponsorship_id == Sponsorship.id,
            isouter=True,
        )
        .join(Donor, Donor.id == Sponsorship.donor_id)
        .where(
            Sponsorship.animal_id == animal_id,
            Sponsorship.status == SponsorshipStatus.ACTIVE,
        )
    )
    rows = (await db.execute(stmt)).all()

    sent = 0
    for _sponsorship, pref, donor in rows:
        # Default: immediate + enabled when no preference row exists
        enabled = pref.notification_enabled if pref else True
        frequency = pref.notification_frequency if pref else SponsorNotificationFrequency.IMMEDIATE

        if not enabled or frequency != SponsorNotificationFrequency.IMMEDIATE:
            continue

        html = _render_update_email(
            animal_name=animal_name,
            title=update.title,
            content=update.content,
            milestone_type=update.milestone_type,
            photo_urls=update.photo_urls or [],
        )
        subject = f"Update about {animal_name}: {update.title}"
        success = await email_service.send_email(
            EmailMessage(to=donor.email, subject=subject, html_body=html)
        )
        if success:
            sent += 1
        else:
            logger.warning(
                "Failed to send sponsor update email to donor_id=%s for update_id=%s",
                donor.id,
                update.id,
            )

    return sent


async def get_or_create_preference(
    db: AsyncSession,
    sponsorship_id: UUID,
) -> SponsorUpdatePreference:
    """Return the SponsorUpdatePreference for a sponsorship, creating defaults if absent."""
    result = await db.execute(
        select(SponsorUpdatePreference).where(
            SponsorUpdatePreference.sponsorship_id == sponsorship_id
        )
    )
    pref = result.scalar_one_or_none()
    if not pref:
        pref = SponsorUpdatePreference(
            sponsorship_id=sponsorship_id,
            notification_enabled=True,
            notification_frequency=SponsorNotificationFrequency.IMMEDIATE,
        )
        db.add(pref)
        await db.flush()
    return pref
