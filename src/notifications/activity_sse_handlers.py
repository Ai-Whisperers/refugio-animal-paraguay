"""SSE handlers for admin real-time activity feed.

Subscribes to ALL domain events on the EventBus and broadcasts them as
human-readable activity items to connected admin SSE clients.

Each event type maps to a Spanish activity message with an icon hint
and category, enabling the frontend to render a rich activity feed.

Registered during app lifespan alongside other notification handlers.
"""

import json
import logging

from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType
from src.services.sse_service import SSEConnectionManager, SSEMessage

logger = logging.getLogger(__name__)

# Map event types to (icon_hint, Spanish message template, category)
# Templates use {key} placeholders filled from event.payload.
_EVENT_DISPLAY_MAP: dict[str, tuple[str, str, str]] = {
    EventType.DONATION_RECEIVED: (
        "dollar-sign",
        "Nueva donacion recibida: {amount} {currency}",
        "donation",
    ),
    EventType.DONATION_REFUNDED: (
        "rotate-ccw",
        "Donacion reembolsada: {amount} {currency}",
        "donation",
    ),
    EventType.DONATION_ALLOCATED: (
        "pie-chart",
        "Donacion asignada a fondo: {fund_category}",
        "donation",
    ),
    EventType.ADOPTION_REQUEST_CREATED: (
        "heart",
        "Nueva solicitud de adopcion recibida",
        "adoption",
    ),
    EventType.ADOPTION_STATUS_CHANGED: (
        "check-circle",
        "Adopcion actualizada: {old_status} -> {new_status}",
        "adoption",
    ),
    EventType.ANIMAL_INTAKE_COMPLETED: (
        "paw-print",
        "Nuevo animal registrado: {name}",
        "animal",
    ),
    EventType.ANIMAL_STATUS_CHANGED: (
        "refresh-cw",
        "Estado de animal actualizado: {name} -> {new_status}",
        "animal",
    ),
    EventType.MEDICAL_ALERT_CREATED: (
        "alert-triangle",
        "Alerta medica creada",
        "medical",
    ),
    EventType.MEDICAL_RECORD_ADDED: (
        "file-plus",
        "Registro medico agregado",
        "medical",
    ),
    EventType.VOLUNTEER_SHIFT_CREATED: (
        "calendar-plus",
        "Turno de voluntario creado",
        "volunteer",
    ),
    EventType.VOLUNTEER_SHIFT_COMPLETED: (
        "calendar-check",
        "Turno de voluntario completado",
        "volunteer",
    ),
    EventType.SUBSCRIPTION_PAYMENT_FAILED: (
        "alert-circle",
        "Pago de suscripcion fallido",
        "subscription",
    ),
    EventType.SUBSCRIPTION_CANCELLED_DUNNING: (
        "x-circle",
        "Suscripcion cancelada por falta de pago",
        "subscription",
    ),
}

# Fallback for unknown event types
_FALLBACK_DISPLAY = ("activity", "Actividad del sistema: {event_type}", "system")


def _format_activity_message(event: DomainEvent) -> str:
    """Build a human-readable Spanish message from a domain event."""
    event_key = event.event_type.value
    _, template, _ = _EVENT_DISPLAY_MAP.get(event_key, _FALLBACK_DISPLAY)

    # Build substitution dict from payload + event metadata
    subs = {**event.payload, "event_type": event_key}
    try:
        return template.format_map(subs)
    except KeyError:
        # If a placeholder is missing, return the template with raw payload info
        return template.split("{")[0].strip() or f"Actividad: {event_key}"


def _get_icon_and_category(event: DomainEvent) -> tuple[str, str]:
    """Return (icon_hint, category) for a domain event."""
    event_key = event.event_type.value
    icon, _, category = _EVENT_DISPLAY_MAP.get(event_key, _FALLBACK_DISPLAY)
    return icon, category


class ActivitySSEHandlers:
    """Handles all domain events and broadcasts them as activity feed items via SSE.

    Usage:
        handlers = ActivitySSEHandlers(sse_manager)
        handlers.register(event_bus)
    """

    def __init__(self, sse_manager: SSEConnectionManager) -> None:
        self._sse_manager = sse_manager

    def register(self, bus: EventBus) -> None:
        """Subscribe to all domain events on the event bus."""
        for event_type in EventType:
            bus.subscribe(event_type, self._on_event)
        logger.info(
            "ActivitySSEHandlers registered for %d event types",
            len(EventType),
        )

    async def _on_event(self, event: DomainEvent) -> None:
        """Handle any domain event by broadcasting an activity SSE message."""
        message_text = _format_activity_message(event)
        icon, category = _get_icon_and_category(event)

        activity_data = {
            "type": "activity",
            "event_type": event.event_type.value,
            "category": category,
            "icon": icon,
            "message": message_text,
            "aggregate_id": str(event.aggregate_id) if event.aggregate_id else None,
            "aggregate_type": event.aggregate_type,
            "actor_id": str(event.actor_id) if event.actor_id else None,
            "timestamp": event.timestamp.isoformat(),
        }

        sse_message = SSEMessage(
            event="activity",
            data=json.dumps(activity_data),
        )

        delivered = await self._sse_manager.broadcast(sse_message)
        if delivered > 0:
            logger.debug(
                "Activity SSE broadcast: %s delivered=%d",
                event.event_type.value,
                delivered,
            )
