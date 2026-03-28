"""Unit tests for donation SSE notification handlers."""

import json
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from src.events.types import DomainEvent, EventType
from src.notifications.donation_sse_handlers import DonationSSEHandlers
from src.services.sse_service import SSEConnectionManager, SSEMessage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_donation_event(
    amount: str = "100.00",
    currency: str = "EUR",
    donor_id: str | None = None,
) -> DomainEvent:
    """Create a donation.received domain event."""
    return DomainEvent(
        event_type=EventType.DONATION_RECEIVED,
        payload={
            "amount": amount,
            "currency": currency,
            "donor_id": donor_id,
        },
        aggregate_id=uuid4(),
        aggregate_type="donation",
    )


# ---------------------------------------------------------------------------
# DonationSSEHandlers tests
# ---------------------------------------------------------------------------


class TestDonationSSEHandlers:
    """Tests for the SSE donation event handler."""

    def test_register_subscribes_to_donation_received(self) -> None:
        manager = SSEConnectionManager()
        handlers = DonationSSEHandlers(manager)
        bus = MagicMock()
        handlers.register(bus)
        bus.subscribe.assert_called_once_with(
            EventType.DONATION_RECEIVED, handlers.on_donation_received
        )

    @pytest.mark.asyncio
    async def test_on_donation_received_broadcasts(self) -> None:
        manager = SSEConnectionManager()
        conn = manager.connect()
        handlers = DonationSSEHandlers(manager)

        event = _make_donation_event(amount="50.00", currency="PYG")
        await handlers.on_donation_received(event)

        assert conn.queue.qsize() == 1
        msg = conn.queue.get_nowait()
        assert isinstance(msg, SSEMessage)
        assert msg.event == "donation"

        data = json.loads(msg.data)
        assert data["type"] == "donation_received"
        assert data["amount"] == "50.00"
        assert data["currency"] == "PYG"
        assert data["timestamp"] == event.timestamp.isoformat()

    @pytest.mark.asyncio
    async def test_on_donation_received_includes_donor_id(self) -> None:
        manager = SSEConnectionManager()
        conn = manager.connect()
        handlers = DonationSSEHandlers(manager)

        donor_id = str(uuid4())
        event = _make_donation_event(donor_id=donor_id)
        await handlers.on_donation_received(event)

        msg = conn.queue.get_nowait()
        data = json.loads(msg.data)
        assert data["donor_id"] == donor_id

    @pytest.mark.asyncio
    async def test_on_donation_received_no_connections(self) -> None:
        manager = SSEConnectionManager()
        handlers = DonationSSEHandlers(manager)

        event = _make_donation_event()
        # Should not raise even with no connections
        await handlers.on_donation_received(event)

    @pytest.mark.asyncio
    async def test_message_format(self) -> None:
        manager = SSEConnectionManager()
        conn = manager.connect()
        handlers = DonationSSEHandlers(manager)

        event = _make_donation_event(amount="200.00", currency="EUR")
        await handlers.on_donation_received(event)

        msg = conn.queue.get_nowait()
        data = json.loads(msg.data)
        assert data["message"] == "Donation received: 200.00 EUR"
        assert data["donation_id"] == str(event.aggregate_id)
