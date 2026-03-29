"""Service layer for email campaign open/click event tracking.

Records engagement events (opens, clicks) from tracking pixels and
redirect links embedded in outbound campaign emails.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.email_campaign import EmailCampaign, EmailCampaignStatus
from src.db.models.email_campaign_event import EmailCampaignEvent, EventType

logger = logging.getLogger(__name__)


async def record_open(
    db: AsyncSession,
    campaign_id: UUID,
    recipient_email: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    variant: str | None = None,
) -> EmailCampaignEvent:
    """Record an email open event for a campaign.

    Called when a tracking pixel embedded in a campaign email is loaded.
    Silently ignores events for campaigns that are not in SENT or SENDING state
    to filter out test/preview loads.

    Returns the created event.
    """
    campaign = await db.get(EmailCampaign, campaign_id)
    if campaign is None:
        raise ValueError(f"Campaign {campaign_id} not found.")
    if campaign.status not in (EmailCampaignStatus.SENT, EmailCampaignStatus.SENDING):
        raise ValueError(
            f"Campaign {campaign_id} is in status '{campaign.status}' — "
            "tracking only accepted for sent or sending campaigns."
        )

    event = EmailCampaignEvent(
        campaign_id=campaign_id,
        event_type=EventType.OPEN,
        recipient_email=recipient_email,
        ip_address=ip_address,
        user_agent=user_agent,
        variant=variant,
    )
    db.add(event)
    await db.flush()
    logger.info(
        "Open event recorded: campaign_id=%s recipient=%s",
        campaign_id,
        recipient_email or "anonymous",
    )
    return event


async def record_click(
    db: AsyncSession,
    campaign_id: UUID,
    clicked_url: str,
    recipient_email: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    variant: str | None = None,
) -> tuple[EmailCampaignEvent, str]:
    """Record an email click event and return the destination URL.

    Called when a tracking redirect link in a campaign email is followed.
    Returns a tuple of (event, redirect_url) so the API layer can issue the
    HTTP redirect after persisting the event.

    Raises ValueError if campaign is not found or not in a trackable state.
    """
    campaign = await db.get(EmailCampaign, campaign_id)
    if campaign is None:
        raise ValueError(f"Campaign {campaign_id} not found.")
    if campaign.status not in (EmailCampaignStatus.SENT, EmailCampaignStatus.SENDING):
        raise ValueError(
            f"Campaign {campaign_id} is in status '{campaign.status}' — "
            "tracking only accepted for sent or sending campaigns."
        )

    event = EmailCampaignEvent(
        campaign_id=campaign_id,
        event_type=EventType.CLICK,
        recipient_email=recipient_email,
        clicked_url=clicked_url,
        ip_address=ip_address,
        user_agent=user_agent,
        variant=variant,
    )
    db.add(event)
    await db.flush()
    logger.info(
        "Click event recorded: campaign_id=%s url=%s recipient=%s",
        campaign_id,
        clicked_url,
        recipient_email or "anonymous",
    )
    return event, clicked_url


async def get_campaign_stats(
    db: AsyncSession,
    campaign_id: UUID,
) -> dict:
    """Return aggregated open/click statistics for a campaign.

    Returns a dict with:
        opens: total open events
        clicks: total click events
        unique_opens: distinct recipient emails that opened (when tracked)
        unique_clicks: distinct recipient emails that clicked (when tracked)
        open_rate: opens / total_recipients (0.0 when no recipients)
        click_rate: clicks / total_recipients (0.0 when no recipients)
        variant_breakdown: {a: {opens, clicks}, b: {opens, clicks}} if A/B active
    """
    campaign = await db.get(EmailCampaign, campaign_id)
    if campaign is None:
        raise ValueError(f"Campaign {campaign_id} not found.")

    # Aggregate counts by event_type
    result = await db.execute(
        select(
            EmailCampaignEvent.event_type,
            func.count(EmailCampaignEvent.id).label("total"),
            func.count(EmailCampaignEvent.recipient_email.distinct()).label("unique"),
        )
        .where(EmailCampaignEvent.campaign_id == campaign_id)
        .group_by(EmailCampaignEvent.event_type)
    )
    rows = result.all()

    opens = 0
    unique_opens = 0
    clicks = 0
    unique_clicks = 0
    for row in rows:
        if row.event_type == EventType.OPEN:
            opens = row.total
            unique_opens = row.unique
        elif row.event_type == EventType.CLICK:
            clicks = row.total
            unique_clicks = row.unique

    total = campaign.total_recipients or 0
    open_rate = round(opens / total, 4) if total else 0.0
    click_rate = round(clicks / total, 4) if total else 0.0

    # Variant breakdown (only populated when A/B testing was used)
    variant_result = await db.execute(
        select(
            EmailCampaignEvent.variant,
            EmailCampaignEvent.event_type,
            func.count(EmailCampaignEvent.id).label("count"),
        )
        .where(
            EmailCampaignEvent.campaign_id == campaign_id,
            EmailCampaignEvent.variant.is_not(None),
        )
        .group_by(EmailCampaignEvent.variant, EmailCampaignEvent.event_type)
    )
    variant_rows = variant_result.all()
    variant_breakdown: dict = {}
    for vrow in variant_rows:
        v = vrow.variant
        if v not in variant_breakdown:
            variant_breakdown[v] = {"opens": 0, "clicks": 0}
        if vrow.event_type == EventType.OPEN:
            variant_breakdown[v]["opens"] = vrow.count
        elif vrow.event_type == EventType.CLICK:
            variant_breakdown[v]["clicks"] = vrow.count

    return {
        "campaign_id": str(campaign_id),
        "status": campaign.status,
        "total_recipients": total,
        "opens": opens,
        "unique_opens": unique_opens,
        "clicks": clicks,
        "unique_clicks": unique_clicks,
        "open_rate": open_rate,
        "click_rate": click_rate,
        "variant_breakdown": variant_breakdown,
    }
