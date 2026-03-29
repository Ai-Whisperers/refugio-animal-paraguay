"""Service layer for GDPR third-party deletion cascade.

GDPR Article 17(2) requires that controllers notify processors and sub-processors
to erase personal data when a right-to-erasure request is processed. This service
handles third-party deletion for:
  - Stripe: cancel active subscriptions, delete the customer record
  - Email lists: mark all subscriptions as GDPR-deleted (hard removal of member records)

Design principles:
  - Failures in third-party deletion must never block or roll back the core anonymization.
    External API failures are logged and surfaced in the summary, but do not raise.
  - Each third-party operation returns a structured result dict.
  - The caller (process_deletion_request) aggregates results into the overall summary.
"""

import logging
import os
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.email_list import EmailListMember
from src.db.models.subscription import Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)

GDPR_DELETION_REASON = "gdpr_erasure"


def _get_stripe_key() -> str | None:
    """Return configured Stripe secret key, or None if not set."""
    return os.environ.get("STRIPE_SECRET_KEY") or None


async def cancel_active_stripe_subscriptions(
    db: AsyncSession,
    donor_id: UUID,
) -> dict:
    """Cancel all active Stripe subscriptions for a donor.

    Queries local subscription records and cancels each one in Stripe.
    Failures per subscription are logged and counted — they do not abort the cascade.

    Returns:
        dict with keys 'cancelled', 'failed', 'skipped'
          - cancelled: number successfully cancelled in Stripe
          - failed: number that raised a Stripe error
          - skipped: number with no Stripe subscription ID
    """
    result = await db.execute(
        select(Subscription).where(
            Subscription.donor_id == donor_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE]),
        )
    )
    subscriptions = result.scalars().all()

    stats = {"cancelled": 0, "failed": 0, "skipped": 0}

    if not subscriptions:
        logger.info("No active subscriptions found for donor %s", donor_id)
        return stats

    stripe_key = _get_stripe_key()
    if not stripe_key:
        logger.warning(
            "STRIPE_SECRET_KEY not configured — skipping Stripe subscription cancellation "
            "for donor %s",
            donor_id,
        )
        stats["skipped"] = len(subscriptions)
        return stats

    try:
        import stripe

        stripe.api_key = stripe_key
    except ImportError:
        logger.warning(
            "stripe package not installed — skipping Stripe operations for donor %s", donor_id
        )
        stats["skipped"] = len(subscriptions)
        return stats

    for subscription in subscriptions:
        stripe_sub_id = subscription.stripe_subscription_id
        if not stripe_sub_id:
            stats["skipped"] += 1
            continue

        try:
            stripe.Subscription.cancel(stripe_sub_id)
            # Mark local record as cancelled
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.now(UTC)
            await db.flush()
            stats["cancelled"] += 1
            logger.info(
                "Cancelled Stripe subscription %s for donor %s (GDPR erasure)",
                stripe_sub_id,
                donor_id,
            )
        except Exception as exc:
            # External API failures must never abort the GDPR deletion
            stats["failed"] += 1
            logger.error(
                "Failed to cancel Stripe subscription %s for donor %s: %s",
                stripe_sub_id,
                donor_id,
                exc,
            )

    return stats


async def delete_stripe_customer(
    donor_id: UUID,
    stripe_customer_id: str,
) -> bool:
    """Delete a Stripe customer record.

    Stripe customer deletion removes all payment methods and billing data.
    Returns True if deletion succeeded, False on error.
    """
    stripe_key = _get_stripe_key()
    if not stripe_key:
        logger.warning(
            "STRIPE_SECRET_KEY not configured — skipping Stripe customer deletion for donor %s",
            donor_id,
        )
        return False

    try:
        import stripe

        stripe.api_key = stripe_key
        stripe.Customer.delete(stripe_customer_id)
        logger.info(
            "Deleted Stripe customer %s for donor %s (GDPR erasure)",
            stripe_customer_id,
            donor_id,
        )
        return True
    except ImportError:
        logger.warning("stripe package not installed — skipping Stripe customer deletion")
        return False
    except Exception as exc:
        logger.error(
            "Failed to delete Stripe customer %s for donor %s: %s",
            stripe_customer_id,
            donor_id,
            exc,
        )
        return False


async def remove_from_email_lists(
    db: AsyncSession,
    email: str,
) -> int:
    """Remove a user from all email lists by hard-deleting their member records.

    GDPR erasure requires complete removal from marketing lists, not just
    unsubscription (which would still store the email address).
    Returns count of deleted member records.
    """
    if not email or email.endswith("@anonymized.invalid"):
        # Email was already anonymized — use source_id lookup won't work;
        # this is a best-effort operation on pre-anonymization email
        logger.info("Email already anonymized — skipping email list removal")
        return 0

    result = await db.execute(delete(EmailListMember).where(EmailListMember.email == email.lower()))
    count = result.rowcount
    if count > 0:
        logger.info(
            "Removed %d email list member records for email %s (GDPR erasure)",
            count,
            email,
        )
    return count


async def process_third_party_deletion(
    db: AsyncSession,
    donor_id: UUID | None,
    donor_email: str | None,
    stripe_customer_id: str | None,
) -> dict:
    """Orchestrate third-party deletion cascade for a GDPR erasure request.

    This should be called BEFORE the donor record is anonymized, so that
    the email address is still available for email list removal.

    Args:
        db: Async database session
        donor_id: Donor ID to cancel subscriptions for (may be None)
        donor_email: Donor's current email address for email list removal (may be None)
        stripe_customer_id: Stripe customer ID to delete (may be None)

    Returns:
        dict with keys:
          - stripe_subscriptions_cancelled: int
          - stripe_subscriptions_failed: int
          - stripe_customer_deleted: bool
          - email_lists_removed: int
    """
    summary: dict = {
        "stripe_subscriptions_cancelled": 0,
        "stripe_subscriptions_failed": 0,
        "stripe_customer_deleted": False,
        "email_lists_removed": 0,
    }

    # Step 1: Cancel active Stripe subscriptions
    if donor_id is not None:
        sub_stats = await cancel_active_stripe_subscriptions(db, donor_id)
        summary["stripe_subscriptions_cancelled"] = sub_stats["cancelled"]
        summary["stripe_subscriptions_failed"] = sub_stats["failed"]

    # Step 2: Delete Stripe customer record (removes payment methods/billing data)
    if stripe_customer_id:
        summary["stripe_customer_deleted"] = await delete_stripe_customer(
            donor_id or UUID(int=0),
            stripe_customer_id,
        )

    # Step 3: Remove from all email lists
    if donor_email:
        summary["email_lists_removed"] = await remove_from_email_lists(db, donor_email)

    logger.info(
        "Third-party GDPR cascade complete for donor %s: %s",
        donor_id,
        summary,
    )
    return summary
