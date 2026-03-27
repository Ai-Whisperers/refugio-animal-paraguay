"""Dunning notification service for failed recurring payments.

Sends tiered email notifications to donors when their subscription
payments fail:
  - First notice (attempt 1): Informational — payment failed, retry pending
  - Second notice (attempt 2): Urgent — please update payment method
  - Final notice (attempt 3+): Subscription cancelled

All notification methods are fire-and-forget: errors are logged but never
re-raised so that a failed notification does not block webhook processing.
"""

import logging
from uuid import UUID

from sqlalchemy import select

from src.db.models.donation import Donor
from src.db.models.subscription import Subscription
from src.db.session import get_async_session
from src.notifications.service import EmailMessage, EmailService
from src.notifications.templates import TemplateRenderer

logger = logging.getLogger(__name__)

SUPPORT_EMAIL = "info@refugioanimalparaguay.org"

# Template names for each dunning tier
TEMPLATE_FIRST_NOTICE = "dunning_first_notice"
TEMPLATE_SECOND_NOTICE = "dunning_second_notice"
TEMPLATE_FINAL_NOTICE = "dunning_final_notice"

# Email subjects for each tier
SUBJECT_FIRST_NOTICE = "Payment issue with your recurring donation"
SUBJECT_SECOND_NOTICE = "Action required: Payment still failing"
SUBJECT_FINAL_NOTICE = "Your recurring donation has been cancelled"


def _format_interval_label(interval: str) -> str:
    """Convert interval code to human-readable label."""
    labels = {
        "month": "monthly",
        "year": "yearly",
    }
    return labels.get(interval, interval)


def _format_amount(amount_cents: int, currency: str) -> str:
    """Format amount from cents to display string."""
    amount = amount_cents / 100
    if currency.upper() == "PYG":
        return f"{amount:,.0f}"
    return f"{amount:.2f}"


class DunningService:
    """Sends tiered dunning emails based on failed payment count.

    Constructed once at application startup and stored on ``app.state``
    so webhook handlers can retrieve it.
    """

    def __init__(
        self,
        email_service: EmailService,
        renderer: TemplateRenderer,
        max_attempts: int = 3,
    ) -> None:
        self._email = email_service
        self._renderer = renderer
        self._max_attempts = max_attempts

    async def send_dunning_email(
        self,
        subscription_id: UUID | str,
        failed_count: int,
        error_message: str | None = None,
    ) -> str:
        """Send the appropriate dunning email based on the failure count.

        Args:
            subscription_id: Local subscription UUID.
            failed_count: Number of consecutive failed payment attempts.
            error_message: Stripe error message from the failed charge.

        Returns:
            Result string: "first_notice_sent", "second_notice_sent",
            "final_notice_sent", or "dunning_skipped".
        """
        try:
            donor, subscription = await self._lookup_subscription_and_donor(
                subscription_id
            )
            if donor is None or subscription is None:
                logger.warning(
                    "dunning: could not resolve donor/subscription for %s, skipping",
                    subscription_id,
                )
                return "dunning_skipped"

            amount_display = _format_amount(
                subscription.amount_cents, subscription.currency
            )
            interval_label = _format_interval_label(subscription.interval)

            base_context = {
                "donor_name": donor.full_name,
                "amount": amount_display,
                "currency": subscription.currency.upper(),
                "interval_label": interval_label,
                "support_email": SUPPORT_EMAIL,
                "error_message": error_message,
                "attempt_number": failed_count,
                "max_attempts": self._max_attempts,
            }

            if failed_count >= self._max_attempts:
                return await self._send_final_notice(donor.email, base_context)
            elif failed_count == 2:
                return await self._send_second_notice(donor.email, base_context)
            else:
                return await self._send_first_notice(donor.email, base_context)

        except Exception as exc:
            logger.exception(
                "dunning: failed to send email for subscription %s: %s",
                subscription_id,
                exc,
            )
            return "dunning_error"

    async def _send_first_notice(
        self, to_email: str, context: dict
    ) -> str:
        """Send first payment failure notification."""
        html = self._renderer.render(TEMPLATE_FIRST_NOTICE, context)
        await self._email.send_email(
            EmailMessage(
                to=to_email,
                subject=SUBJECT_FIRST_NOTICE,
                html_body=html,
            )
        )
        logger.info("dunning: first notice sent to %s", to_email)
        return "first_notice_sent"

    async def _send_second_notice(
        self, to_email: str, context: dict
    ) -> str:
        """Send second payment failure notification."""
        html = self._renderer.render(TEMPLATE_SECOND_NOTICE, context)
        await self._email.send_email(
            EmailMessage(
                to=to_email,
                subject=SUBJECT_SECOND_NOTICE,
                html_body=html,
            )
        )
        logger.info("dunning: second notice sent to %s", to_email)
        return "second_notice_sent"

    async def _send_final_notice(
        self, to_email: str, context: dict
    ) -> str:
        """Send final cancellation notification."""
        html = self._renderer.render(TEMPLATE_FINAL_NOTICE, context)
        await self._email.send_email(
            EmailMessage(
                to=to_email,
                subject=SUBJECT_FINAL_NOTICE,
                html_body=html,
            )
        )
        logger.info("dunning: final notice sent to %s", to_email)
        return "final_notice_sent"

    @staticmethod
    async def _lookup_subscription_and_donor(
        subscription_id: UUID | str,
    ) -> tuple["Donor | None", "Subscription | None"]:
        """Fetch a Subscription and its associated Donor."""
        try:
            uid = (
                UUID(str(subscription_id))
                if not isinstance(subscription_id, UUID)
                else subscription_id
            )
            async with get_async_session() as session:
                result = await session.execute(
                    select(Subscription).where(Subscription.id == uid)
                )
                subscription = result.scalar_one_or_none()
                if subscription is None:
                    return None, None

                donor_result = await session.execute(
                    select(Donor).where(Donor.id == subscription.donor_id)
                )
                donor = donor_result.scalar_one_or_none()
                return donor, subscription
        except Exception as exc:
            logger.exception(
                "dunning: DB lookup failed for subscription %s: %s",
                subscription_id,
                exc,
            )
            return None, None
