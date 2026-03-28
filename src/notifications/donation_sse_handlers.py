"""SSE handlers for real-time donation notifications.

Bridges the EventBus to SSE connections, broadcasting donation events
to connected admin clients for real-time dashboard updates.

Registered during app lifespan alongside other notification handlers.
"""

import json
import logging

from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType
from src.services.sse_service import SSEConnectionManager, SSEMessage

logger = logging.getLogger(__name__)


class DonationSSEHandlers:
    """Handles donation events and broadcasts them via SSE.

    Usage:
        handlers = DonationSSEHandlers(sse_manager)
        handlers.register(event_bus)
    """

    def __init__(self, sse_manager: SSEConnectionManager) -> None:
        self._sse_manager = sse_manager

    def register(self, bus: EventBus) -> None:
        """Subscribe to donation events on the event bus."""
        bus.subscribe(EventType.DONATION_RECEIVED, self.on_donation_received)
        logger.info("DonationSSEHandlers registered on event bus")

    async def on_donation_received(self, event: DomainEvent) -> None:
        """Handle a donation.received event by broadcasting via SSE."""
        payload = event.payload
        amount = payload.get("amount", "0")
        currency = payload.get("currency", "PYG")
        donor_id = payload.get("donor_id")

        notification_data = {
            "type": "donation_received",
            "donation_id": str(event.aggregate_id) if event.aggregate_id else None,
            "amount": amount,
            "currency": currency,
            "donor_id": donor_id,
            "timestamp": event.timestamp.isoformat(),
            "message": f"Donation received: {amount} {currency}",
        }

        message = SSEMessage(
            event="donation",
            data=json.dumps(notification_data),
        )

        delivered = await self._sse_manager.broadcast(message)
        logger.info(
            "Donation SSE notification broadcast: donation=%s amount=%s %s delivered=%d",
            event.aggregate_id,
            amount,
            currency,
            delivered,
        )
