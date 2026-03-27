"""Event bus handlers that send WhatsApp notifications via Twilio.

Handlers subscribe to domain events and dispatch templated WhatsApp messages
to recipients who have WhatsApp-capable phone numbers. All handlers fail
gracefully: errors are logged but never re-raised, so they do not disrupt
the event bus.

Registration::

    handlers = WhatsAppHandlers(whatsapp_service)
    handlers.register(event_bus)
"""

import logging
from uuid import UUID

from sqlalchemy import select

from src.db.session import get_async_session
from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType
from src.notifications.whatsapp_service import WhatsAppMessage, WhatsAppService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Message templates
# Pre-approve these bodies with Meta via the Twilio console before going live.
# In production, replace these with the exact approved template text.
# ---------------------------------------------------------------------------

TEMPLATE_ADOPTION_STATUS_UPDATE = (
    "Hola {adopter_name}! Tu solicitud de adopción para {animal_name} ha cambiado "
    "de estado: {old_status} → {new_status}. Para más información contacta al refugio."
)

TEMPLATE_SHIFT_CONFIRMATION = (
    "Hola {volunteer_name}! Tu turno de voluntariado el {shift_date} a las {shift_time} "
    "ha sido confirmado. ¡Gracias por tu apoyo al Refugio Animal Paraguay!"
)

TEMPLATE_SHIFT_REMINDER = (
    "Recordatorio: tienes un turno de voluntariado mañana {shift_date} a las {shift_time}. "
    "¡Te esperamos en el Refugio Animal Paraguay!"
)

TEMPLATE_SHIFT_CANCELLATION = (
    "Aviso importante: tu turno de voluntariado el {shift_date} ha sido cancelado "
    "por el personal del refugio. Lamentamos los inconvenientes causados."
)


class WhatsAppHandlers:
    """Event handlers that deliver WhatsApp messages for key shelter events."""

    def __init__(self, whatsapp_service: WhatsAppService) -> None:
        self._wa = whatsapp_service

    def register(self, bus: EventBus) -> None:
        """Subscribe all WhatsApp handlers to the event bus."""
        bus.subscribe(EventType.ADOPTION_STATUS_CHANGED, self.on_adoption_status_changed)
        bus.subscribe(EventType.VOLUNTEER_SHIFT_CREATED, self.on_volunteer_shift_created)
        bus.subscribe(EventType.VOLUNTEER_SHIFT_COMPLETED, self.on_volunteer_shift_completed)
        logger.info("WhatsApp handlers registered on event bus")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    async def on_adoption_status_changed(self, event: DomainEvent) -> None:
        """Send WhatsApp adoption status update to the adopter."""
        if not self._wa.is_enabled:
            return
        try:
            payload = event.payload
            phone = payload.get("adopter_phone")
            if not phone:
                # No phone number — skip silently (email handler covers it)
                return

            body = TEMPLATE_ADOPTION_STATUS_UPDATE.format(
                adopter_name=payload.get("adopter_name", "Estimado/a"),
                animal_name=payload.get("animal_name", "el animal"),
                old_status=payload.get("old_status", "pendiente"),
                new_status=payload.get("new_status", "actualizado"),
            )
            await self._wa.send_message(WhatsAppMessage(to=phone, body=body))
        except Exception:
            logger.exception(
                "WhatsApp adoption status handler failed for event_id=%s",
                event.id,
            )

    async def on_volunteer_shift_created(self, event: DomainEvent) -> None:
        """Send WhatsApp shift confirmation when a volunteer is scheduled."""
        if not self._wa.is_enabled:
            return
        try:
            payload = event.payload
            phone = payload.get("volunteer_phone")
            if not phone:
                return

            cancellation = payload.get("cancelled", False)
            if cancellation:
                template = TEMPLATE_SHIFT_CANCELLATION
                body = template.format(
                    shift_date=payload.get("shift_date", "la fecha indicada"),
                )
            else:
                body = TEMPLATE_SHIFT_CONFIRMATION.format(
                    volunteer_name=payload.get("volunteer_name", "Voluntario/a"),
                    shift_date=payload.get("shift_date", "la fecha indicada"),
                    shift_time=payload.get("shift_time", "la hora indicada"),
                )
            await self._wa.send_message(WhatsAppMessage(to=phone, body=body))
        except Exception:
            logger.exception(
                "WhatsApp shift confirmation handler failed for event_id=%s",
                event.id,
            )

    async def on_volunteer_shift_completed(self, event: DomainEvent) -> None:
        """Send WhatsApp shift reminder (repurposed from shift_completed for reminders)."""
        if not self._wa.is_enabled:
            return
        try:
            payload = event.payload
            phone = payload.get("volunteer_phone")
            if not phone:
                return

            # This event type is used for reminder dispatch by the scheduler.
            body = TEMPLATE_SHIFT_REMINDER.format(
                shift_date=payload.get("shift_date", "mañana"),
                shift_time=payload.get("shift_time", "la hora indicada"),
            )
            await self._wa.send_message(WhatsAppMessage(to=phone, body=body))
        except Exception:
            logger.exception(
                "WhatsApp shift reminder handler failed for event_id=%s",
                event.id,
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _lookup_adopter_phone(
        adoption_request_id: UUID,
    ) -> tuple[str | None, str | None, str | None, str | None]:
        """Look up adopter phone, name, and animal name from adoption_request_id.

        Returns (phone, adopter_name, animal_name, None) or Nones on failure.
        """
        try:
            from src.db.models.adopter import Adopter
            from src.db.models.adoption_request import AdoptionRequest
            from src.db.models.animal import Animal

            async with get_async_session() as session:
                result = await session.execute(
                    select(AdoptionRequest).where(AdoptionRequest.id == adoption_request_id)
                )
                request = result.scalar_one_or_none()
                if not request:
                    return None, None, None, None

                adopter_result = await session.execute(
                    select(Adopter).where(Adopter.id == request.adopter_id)
                )
                adopter = adopter_result.scalar_one_or_none()

                animal_result = await session.execute(
                    select(Animal).where(Animal.id == request.animal_id)
                )
                animal = animal_result.scalar_one_or_none()

                return (
                    getattr(adopter, "phone", None) if adopter else None,
                    adopter.full_name if adopter else None,
                    animal.name if animal else None,
                    None,
                )
        except Exception:
            logger.exception(
                "DB lookup failed for adoption_request_id=%s in WhatsApp handler",
                adoption_request_id,
            )
            return None, None, None, None
