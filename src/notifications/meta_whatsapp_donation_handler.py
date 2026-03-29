"""WhatsApp donation receipt handler using Meta Cloud API (RAP-203).

Subscribes to DONATION_RECEIVED domain events and sends a pre-approved WhatsApp
template receipt message to donors who have a phone number on file.

Template name used: ``donation_receipt``
Register this template in Meta Business Manager before going live.
Expected body variables (positional):
  {{1}} — donor first name
  {{2}} — donation amount (formatted, e.g. "50.00")
  {{3}} — currency code (e.g. "EUR", "PYG")
  {{4}} — receipt number (or empty string if not available)

Registration::

    handler = MetaWhatsAppDonationHandler(meta_whatsapp_service)
    handler.register(event_bus)
"""

from __future__ import annotations

import logging
from uuid import UUID

from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType
from src.notifications.meta_whatsapp_service import MetaTemplateMessage, MetaWhatsAppService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DONATION_RECEIPT_TEMPLATE_NAME = "donation_receipt"
DONATION_RECEIPT_TEMPLATE_LANGUAGE = "es"


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


class MetaWhatsAppDonationHandler:
    """Event handler that sends WhatsApp donation receipt messages via Meta Cloud API.

    Subscribes to DONATION_RECEIVED events. On each event it:
    1. Looks up the donor's phone, first name, amount, currency, and receipt number.
    2. Sends a pre-approved ``donation_receipt`` template message via MetaWhatsAppService.

    Fails gracefully — errors are logged but never re-raised, so they do not
    disrupt the event bus or the payment flow.
    """

    def __init__(self, meta_whatsapp_service: MetaWhatsAppService) -> None:
        self._meta_wa = meta_whatsapp_service

    def register(self, bus: EventBus) -> None:
        """Subscribe to the DONATION_RECEIVED event on the given bus."""
        bus.subscribe(EventType.DONATION_RECEIVED, self.on_donation_received)
        logger.info("MetaWhatsAppDonationHandler registered on event bus")

    # ------------------------------------------------------------------
    # Handler
    # ------------------------------------------------------------------

    async def on_donation_received(self, event: DomainEvent) -> None:
        """Send WhatsApp donation receipt to the donor.

        Skips silently when:
        - Meta WhatsApp integration is disabled
        - aggregate_id is missing from the event
        - Donor has no phone number registered
        - DB lookup fails (logged separately)
        """
        if not self._meta_wa.is_enabled:
            return

        if event.aggregate_id is None:
            logger.warning("RAP-203: DONATION_RECEIVED event missing aggregate_id — skipping")
            return

        donation_id: UUID = event.aggregate_id

        try:
            phone, first_name, amount_display, currency, receipt_number = (
                await _lookup_donor_whatsapp_context(donation_id)
            )
        except Exception as exc:
            logger.error(
                "RAP-203: DB lookup failed for donation_id=%s: %s",
                donation_id,
                exc,
            )
            return

        if not phone:
            logger.debug(
                "RAP-203: No phone for donation_id=%s — skipping WhatsApp receipt",
                donation_id,
            )
            return

        # Prefer event payload values for amount/currency (same as email handler)
        payload_amount = event.payload.get("amount", amount_display or "0.00")
        payload_currency = event.payload.get("currency", currency or "EUR")

        message = MetaTemplateMessage(
            to=phone,
            template_name=DONATION_RECEIPT_TEMPLATE_NAME,
            language_code=DONATION_RECEIPT_TEMPLATE_LANGUAGE,
            components=[
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": first_name or "Estimado/a"},
                        {"type": "text", "text": payload_amount},
                        {"type": "text", "text": payload_currency},
                        {"type": "text", "text": receipt_number or ""},
                    ],
                }
            ],
        )

        try:
            success = await self._meta_wa.send_template(message)
            if not success:
                logger.warning(
                    "RAP-203: Meta WhatsApp delivery failed for donation_id=%s to=%s",
                    donation_id,
                    phone,
                )
        except Exception as exc:
            logger.exception(
                "RAP-203: Unexpected error sending WhatsApp receipt for donation_id=%s: %s",
                donation_id,
                exc,
            )


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


async def _lookup_donor_whatsapp_context(
    donation_id: UUID,
) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    """Return (phone, first_name, amount_display, currency, receipt_number) for a donation.

    Returns (None, None, None, None, None) when the donation or donor is not found.
    Raises on unexpected DB errors so the caller can log them.
    """
    from sqlalchemy import select

    from src.db.models.donation import Donation, Donor
    from src.db.session import get_async_session

    async with get_async_session() as session:
        result = await session.execute(select(Donation).where(Donation.id == donation_id))
        donation = result.scalar_one_or_none()
        if donation is None:
            return None, None, None, None, None

        donor: Donor | None = None
        if donation.donor_id is not None:
            donor_result = await session.execute(select(Donor).where(Donor.id == donation.donor_id))
            donor = donor_result.scalar_one_or_none()

        phone = getattr(donor, "phone", None) if donor else None
        full_name = getattr(donor, "full_name", None) if donor else None
        # Use first name only for a friendlier greeting
        first_name = full_name.split()[0] if full_name else None
        amount_display = f"{donation.amount_cents / 100:.2f}"
        receipt_number = getattr(donation, "receipt_number", None)

        return phone, first_name, amount_display, donation.currency, receipt_number
