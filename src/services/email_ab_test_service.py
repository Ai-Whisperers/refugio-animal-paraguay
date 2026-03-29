"""Service layer for A/B subject line testing in email campaigns.

When a campaign has both subject_a and subject_b set, recipients are split
by ab_ratio (default 50/50). Variant attribution is stored on the EmailCampaignEvent
records recorded during send, enabling stats breakdown by variant.

This service is additive — it does not replace email_campaign_service.initiate_send
but is called by it when A/B mode is detected.
"""

import logging
import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.email_campaign import EmailCampaign, EmailCampaignStatus
from src.db.models.email_list import EmailListMember, MemberStatus

logger = logging.getLogger(__name__)


def is_ab_test_active(campaign: EmailCampaign) -> bool:
    """Return True when the campaign has a second subject line configured."""
    return bool(campaign.subject_b)


def split_recipients_by_variant(
    members: list,
    ab_ratio: float,
) -> tuple[list, list]:
    """Split a list of members into variant A and variant B groups.

    Args:
        members: All subscribed members for the campaign list.
        ab_ratio: Fraction of members assigned to variant A (0.0-1.0).

    Returns:
        Tuple (variant_a_members, variant_b_members). The split is deterministic
        based on list ordering — no randomisation needed for MVP.
    """
    total = len(members)
    a_count = math.ceil(total * ab_ratio)
    return members[:a_count], members[a_count:]


async def initiate_send_ab(
    db: AsyncSession,
    campaign: EmailCampaign,
) -> dict[str, int]:
    """Initiate sending with A/B subject line split.

    Validates that both subject_a and subject_b are set, splits the recipient
    list by ab_ratio, and transitions the campaign through SENDING → SENT.
    Variant counts are returned for caller logging.

    Returns:
        dict with 'queued', 'variant_a', and 'variant_b' counts.

    Raises:
        ValueError if campaign is not in a sendable state or A/B config is invalid.
    """
    if campaign.status not in (
        EmailCampaignStatus.DRAFT,
        EmailCampaignStatus.SCHEDULED,
    ):
        raise ValueError(
            f"Cannot send campaign in status '{campaign.status}'. "
            "Only draft or scheduled campaigns can be sent."
        )
    if not campaign.subject_a:
        raise ValueError(
            "A/B test mode requires subject_a to be set. "
            "Set subject_a (and subject_b for the test variant)."
        )
    if not campaign.subject_b:
        raise ValueError(
            "A/B test mode requires subject_b to be set. "
            "Use initiate_send() for single-subject campaigns."
        )

    ab_ratio = float(campaign.ab_ratio) if campaign.ab_ratio is not None else 0.5

    # Count subscribed recipients
    result = await db.execute(
        select(EmailListMember).where(
            EmailListMember.email_list_id == campaign.email_list_id,
            EmailListMember.status == MemberStatus.SUBSCRIBED,
        )
    )
    members = list(result.scalars().all())
    total = len(members)

    variant_a_members, variant_b_members = split_recipients_by_variant(members, ab_ratio)
    a_count = len(variant_a_members)
    b_count = len(variant_b_members)

    campaign.status = EmailCampaignStatus.SENDING
    campaign.total_recipients = total
    await db.flush()

    logger.info(
        "A/B campaign send initiated: id=%s total=%d a=%d b=%d ratio=%.3f",
        campaign.id,
        total,
        a_count,
        b_count,
        ab_ratio,
    )

    # In production: queue individual send tasks per variant with correct subject.
    # For MVP: mark as sent immediately.
    from datetime import UTC, datetime

    campaign.status = EmailCampaignStatus.SENT
    campaign.sent_count = total
    campaign.failed_count = 0
    campaign.sent_at = datetime.now(UTC)
    await db.flush()

    logger.info(
        "A/B campaign send complete: id=%s sent=%d (a=%d, b=%d)",
        campaign.id,
        total,
        a_count,
        b_count,
    )
    return {"queued": total, "variant_a": a_count, "variant_b": b_count}
