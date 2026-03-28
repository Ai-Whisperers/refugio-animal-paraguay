"""Impact notification service for donor transparency.

Notifies donors when their donations are allocated to specific expenses,
giving them visibility into how their contributions are being used.
Listens for DONATION_ALLOCATED events and sends impact notifications
via email and in-app channels.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType

logger = logging.getLogger(__name__)

# Template name for impact notification emails
IMPACT_EMAIL_TEMPLATE = "donation_impact"

# In-app notification type
IMPACT_NOTIFICATION_TYPE = "donation_impact"


@dataclass
class ImpactNotification:
    """Structured impact notification for a donor."""

    donor_id: UUID | None
    donor_email: str | None
    donation_id: UUID
    expense_description: str
    amount_cents: int
    currency: str
    expense_id: UUID


def _build_impact_notification(event: DomainEvent) -> ImpactNotification | None:
    """Extract impact notification details from a DonationAllocated event.

    Returns None if the event lacks required donor information.
    """
    payload = event.payload
    donor_id_str = payload.get("donor_id")
    donor_email = payload.get("donor_email")

    if not donor_id_str and not donor_email:
        # Anonymous donation — no one to notify
        logger.debug("Skipping impact notification for anonymous donation %s", event.aggregate_id)
        return None

    return ImpactNotification(
        donor_id=UUID(donor_id_str) if donor_id_str else None,
        donor_email=donor_email,
        donation_id=UUID(payload["donation_id"]),
        expense_description=payload["expense_description"],
        amount_cents=payload["amount_cents"],
        currency=payload["currency"],
        expense_id=UUID(payload["expense_id"]),
    )


def _format_amount(amount_cents: int, currency: str) -> str:
    """Format amount in cents to human-readable string."""
    if currency == "PYG":
        # Guaraníes don't use decimal places
        return f"{amount_cents:,} Gs."
    # EUR/USD use 2 decimal places
    major = amount_cents // 100
    minor = amount_cents % 100
    symbol = "€" if currency == "EUR" else "$"
    return f"{symbol}{major}.{minor:02d}"


class ImpactNotificationHandlers:
    """Event handlers for donation impact notifications.

    Registers on the event bus to listen for DONATION_ALLOCATED events
    and dispatches impact notifications to donors via configured channels.
    """

    def __init__(
        self,
        email_service: object | None = None,
        template_renderer: object | None = None,
    ) -> None:
        self._email_service = email_service
        self._template_renderer = template_renderer
        self._notifications_sent: list[ImpactNotification] = []

    def register(self, event_bus: EventBus) -> None:
        """Register handlers on the event bus."""
        event_bus.subscribe(EventType.DONATION_ALLOCATED, self._handle_donation_allocated)

    async def _handle_donation_allocated(self, event: DomainEvent) -> None:
        """Handle DONATION_ALLOCATED event — notify the donor."""
        notification = _build_impact_notification(event)
        if notification is None:
            return

        self._notifications_sent.append(notification)

        formatted_amount = _format_amount(notification.amount_cents, notification.currency)

        logger.info(
            "Impact notification: donation %s allocated %s to '%s' (donor=%s)",
            notification.donation_id,
            formatted_amount,
            notification.expense_description,
            notification.donor_id or "email-only",
        )

        # Send email notification if email service is configured
        if self._email_service and notification.donor_email:
            try:
                await self._send_impact_email(notification, formatted_amount)
            except Exception:
                logger.warning(
                    "Failed to send impact email for donation %s",
                    notification.donation_id,
                    exc_info=True,
                )

    async def _send_impact_email(
        self,
        notification: ImpactNotification,
        formatted_amount: str,
    ) -> None:
        """Send impact notification email to donor."""
        if not notification.donor_email:
            return

        # Build template context
        context = {
            "amount": formatted_amount,
            "expense_description": notification.expense_description,
            "currency": notification.currency,
        }

        logger.debug(
            "Sending impact email to %s for donation %s",
            notification.donor_email,
            notification.donation_id,
        )

        # Email sending delegated to the email service
        # Template rendering delegated to the template renderer
        # Both are injected and may be None in test/dev environments
        if hasattr(self._email_service, "send_template"):
            await self._email_service.send_template(  # type: ignore[union-attr]
                to_email=notification.donor_email,
                template_name=IMPACT_EMAIL_TEMPLATE,
                context=context,
            )

    @property
    def notifications_sent(self) -> list[ImpactNotification]:
        """Access sent notifications (useful for testing)."""
        return list(self._notifications_sent)
