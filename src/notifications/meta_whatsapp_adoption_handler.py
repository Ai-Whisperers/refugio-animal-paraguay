"""WhatsApp adoption status notification handler using Meta Cloud API.

Subscribes to ADOPTION_STATUS_CHANGED domain events and sends pre-approved
WhatsApp template messages to adopters via the Meta Cloud API (RAP-202).

Dependencies:
- MetaWhatsAppService (RAP-200) — sends template messages via Meta Graph API
- WhatsApp template registry (RAP-201) — templates must be approved in Meta

Template name used: ``adoption_status_update``
Register this template in Meta Business Manager before going live.
Expected body variables (positional):
  {{1}} — adopter first name
  {{2}} — animal name
  {{3}} — new status (human-readable)

Registration::

    handler = MetaWhatsAppAdoptionHandler(meta_whatsapp_service)
    handler.register(event_bus)
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select

from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType
from src.notifications.meta_whatsapp_service import MetaTemplateMessage, MetaWhatsAppService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ADOPTION_STATUS_TEMPLATE_NAME = "adoption_status_update"
ADOPTION_STATUS_TEMPLATE_LANGUAGE = "es"

# Human-readable status labels for template variable substitution
_STATUS_LABELS: dict[str, str] = {
    "pending": "pendiente",
    "approved": "aprobada",
    "rejected": "rechazada",
    "cancelled": "cancelada",
}


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


class MetaWhatsAppAdoptionHandler:
    """Event handler that sends WhatsApp adoption status notifications via Meta Cloud API.

    Subscribes to ADOPTION_STATUS_CHANGED events. On each event it:
    1. Looks up the adopter's phone, first name, and animal name from the DB.
    2. Sends a pre-approved template message via MetaWhatsAppService.

    Fails gracefully — errors are logged but never re-raised, so they do not
    disrupt the event bus or the adoption workflow.
    """

    def __init__(self, meta_whatsapp_service: MetaWhatsAppService) -> None:
        self._meta_wa = meta_whatsapp_service

    def register(self, bus: EventBus) -> None:
        """Subscribe to the ADOPTION_STATUS_CHANGED event on the given bus."""
        bus.subscribe(EventType.ADOPTION_STATUS_CHANGED, self.on_adoption_status_changed)
        logger.info("MetaWhatsAppAdoptionHandler registered on event bus")

    # ------------------------------------------------------------------
    # Handler
    # ------------------------------------------------------------------

    async def on_adoption_status_changed(self, event: DomainEvent) -> None:
        """Send WhatsApp template message to the adopter on status change.

        Skips silently when:
        - Meta WhatsApp integration is disabled
        - Adopter has no phone number registered
        - DB lookup fails (logged separately)
        """
        if not self._meta_wa.is_enabled:
            return

        if event.aggregate_id is None:
            logger.warning("RAP-202: ADOPTION_STATUS_CHANGED event missing aggregate_id — skipping")
            return

        adoption_request_id: UUID = event.aggregate_id
        new_status = event.payload.get("new_status", "")

        try:
            phone, first_name, animal_name = await _lookup_adopter_whatsapp_context(
                adoption_request_id
            )
        except Exception as exc:
            logger.error(
                "RAP-202: DB lookup failed for adoption_request_id=%s: %s",
                adoption_request_id,
                exc,
            )
            return

        if not phone:
            # No phone number registered — WhatsApp delivery not possible
            logger.debug(
                "RAP-202: No phone for adoption_request_id=%s — skipping WhatsApp",
                adoption_request_id,
            )
            return

        status_label = _STATUS_LABELS.get(new_status, new_status)

        message = MetaTemplateMessage(
            to=phone,
            template_name=ADOPTION_STATUS_TEMPLATE_NAME,
            language_code=ADOPTION_STATUS_TEMPLATE_LANGUAGE,
            components=[
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": first_name or "Estimado/a"},
                        {"type": "text", "text": animal_name or "el animal"},
                        {"type": "text", "text": status_label},
                    ],
                }
            ],
        )

        try:
            success = await self._meta_wa.send_template(message)
            if not success:
                logger.warning(
                    "RAP-202: Meta WhatsApp delivery failed for adoption_request_id=%s to=%s",
                    adoption_request_id,
                    phone,
                )
        except Exception as exc:
            logger.exception(
                "RAP-202: Unexpected error sending WhatsApp for adoption_request_id=%s: %s",
                adoption_request_id,
                exc,
            )


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


async def _lookup_adopter_whatsapp_context(
    adoption_request_id: UUID,
) -> tuple[str | None, str | None, str | None]:
    """Return (phone, first_name, animal_name) for an adoption request.

    Returns (None, None, None) when the request or related records are not found.
    Raises on unexpected DB errors so the caller can log them.
    """
    from src.db.models.adopter import Adopter
    from src.db.models.adoption_request import AdoptionRequest
    from src.db.models.animal import Animal
    from src.db.session import get_async_session

    async with get_async_session() as session:
        result = await session.execute(
            select(AdoptionRequest).where(AdoptionRequest.id == adoption_request_id)
        )
        adoption_request = result.scalar_one_or_none()
        if adoption_request is None:
            return None, None, None

        adopter_result = await session.execute(
            select(Adopter).where(Adopter.id == adoption_request.adopter_id)
        )
        adopter = adopter_result.scalar_one_or_none()

        animal_result = await session.execute(
            select(Animal).where(Animal.id == adoption_request.animal_id)
        )
        animal = animal_result.scalar_one_or_none()

        phone = getattr(adopter, "phone", None) if adopter else None
        full_name = getattr(adopter, "full_name", None) if adopter else None
        # Use first name only for a friendlier greeting in the template
        first_name = full_name.split()[0] if full_name else None
        animal_name = getattr(animal, "name", None) if animal else None

        return phone, first_name, animal_name
