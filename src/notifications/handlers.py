"""Event bus handlers that trigger email notifications.

Each handler subscribes to a specific domain event type and sends
the appropriate email using the EmailService + TemplateRenderer.

Registration:
    Called from app lifespan via register_notification_handlers().
"""

import logging
from uuid import UUID

from sqlalchemy import select

from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest
from src.db.models.animal import Animal
from src.db.models.donation import Donation, Donor
from src.db.session import get_async_session
from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType
from src.notifications.service import EmailMessage, EmailService
from src.notifications.templates import TemplateRenderer

logger = logging.getLogger(__name__)


class NotificationHandlers:
    """Collection of event handlers that send email notifications.

    Handlers are stateless functions that look up context from the database,
    render a template, and send via EmailService. Each handler is designed
    to fail gracefully: errors are logged but never re-raised, so they
    don't disrupt the event bus.
    """

    def __init__(self, email_service: EmailService, renderer: TemplateRenderer) -> None:
        self._email = email_service
        self._renderer = renderer

    def register(self, bus: EventBus) -> None:
        """Subscribe all notification handlers to the event bus."""
        bus.subscribe(EventType.ADOPTION_STATUS_CHANGED, self.on_adoption_status_changed)
        bus.subscribe(EventType.DONATION_RECEIVED, self.on_donation_received)
        logger.info("Notification handlers registered on event bus")

    async def on_adoption_status_changed(self, event: DomainEvent) -> None:
        """Send email when an adoption request status changes."""
        try:
            payload = event.payload
            aggregate_id = event.aggregate_id
            if not aggregate_id:
                logger.warning("Adoption status changed event missing aggregate_id")
                return

            adopter_email, adopter_name, animal_name = await self._lookup_adoption_context(
                aggregate_id
            )
            if not adopter_email:
                logger.warning(
                    "Could not find adopter email for adoption_request_id=%s",
                    aggregate_id,
                )
                return

            html = self._renderer.render(
                "adoption_status_changed",
                {
                    "adopter_name": adopter_name or "Valued Adopter",
                    "animal_name": animal_name or "your requested animal",
                    "old_status": payload.get("old_status", "unknown"),
                    "new_status": payload.get("new_status", "unknown"),
                },
            )

            new_status = payload.get("new_status", "updated")
            subject = f"Adoption Request Update: {new_status.replace('_', ' ').title()}"

            await self._email.send_email(
                EmailMessage(to=adopter_email, subject=subject, html_body=html)
            )
        except Exception:
            logger.exception(
                "Failed to send adoption status notification for event_id=%s",
                event.id,
            )

    async def on_donation_received(self, event: DomainEvent) -> None:
        """Send thank-you email when a donation is received."""
        try:
            payload = event.payload
            aggregate_id = event.aggregate_id
            if not aggregate_id:
                logger.warning("Donation received event missing aggregate_id")
                return

            donor_email, donor_name, amount, currency, receipt_number = (
                await self._lookup_donation_context(aggregate_id)
            )
            if not donor_email:
                logger.warning(
                    "Could not find donor email for donation_id=%s",
                    aggregate_id,
                )
                return

            # Prefer event payload values, fall back to DB values
            display_amount = payload.get("amount", amount or "0")
            display_currency = payload.get("currency", currency or "PYG")

            html = self._renderer.render(
                "donation_received",
                {
                    "donor_name": donor_name or "Valued Donor",
                    "amount": display_amount,
                    "currency": display_currency,
                    "receipt_number": receipt_number,
                },
            )

            await self._email.send_email(
                EmailMessage(
                    to=donor_email,
                    subject="Thank You for Your Donation!",
                    html_body=html,
                )
            )
        except Exception:
            logger.exception(
                "Failed to send donation notification for event_id=%s",
                event.id,
            )

    @staticmethod
    async def _lookup_adoption_context(
        adoption_request_id: UUID,
    ) -> tuple[str | None, str | None, str | None]:
        """Look up adopter email, name, and animal name from an adoption request ID.

        Returns (email, adopter_name, animal_name) or (None, None, None) on failure.
        """
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(AdoptionRequest).where(AdoptionRequest.id == adoption_request_id)
                )
                request = result.scalar_one_or_none()
                if not request:
                    return None, None, None

                # Load adopter
                adopter_result = await session.execute(
                    select(Adopter).where(Adopter.id == request.adopter_id)
                )
                adopter = adopter_result.scalar_one_or_none()

                # Load animal
                animal_result = await session.execute(
                    select(Animal).where(Animal.id == request.animal_id)
                )
                animal = animal_result.scalar_one_or_none()

                return (
                    adopter.email if adopter else None,
                    adopter.full_name if adopter else None,
                    animal.name if animal else None,
                )
        except Exception:
            logger.exception(
                "DB lookup failed for adoption_request_id=%s",
                adoption_request_id,
            )
            return None, None, None

    @staticmethod
    async def _lookup_donation_context(
        donation_id: UUID,
    ) -> tuple[str | None, str | None, str | None, str | None, str | None]:
        """Look up donor details from a donation ID.

        Returns (email, name, amount, currency, receipt_number) or Nones on failure.
        """
        try:
            async with get_async_session() as session:
                result = await session.execute(select(Donation).where(Donation.id == donation_id))
                donation = result.scalar_one_or_none()
                if not donation:
                    return None, None, None, None, None

                # Load donor
                donor_result = await session.execute(
                    select(Donor).where(Donor.id == donation.donor_id)
                )
                donor = donor_result.scalar_one_or_none()

                amount_display = f"{donation.amount_cents / 100:.2f}"

                return (
                    donor.email if donor else None,
                    donor.full_name if donor else None,
                    amount_display,
                    donation.currency,
                    getattr(donation, "receipt_number", None),
                )
        except Exception:
            logger.exception(
                "DB lookup failed for donation_id=%s",
                donation_id,
            )
            return None, None, None, None, None
