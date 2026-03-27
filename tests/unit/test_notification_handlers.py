"""Unit tests for notification event handlers.

Tests cover:
  - Handler registration on event bus
  - Adoption status changed handler
  - Donation received handler
  - Error handling (missing aggregate_id, DB lookup failures)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType
from src.notifications.handlers import NotificationHandlers
from src.notifications.service import EmailService
from src.notifications.templates import TemplateRenderer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_handlers() -> tuple[NotificationHandlers, MagicMock, MagicMock]:
    """Create a NotificationHandlers with mocked email service and renderer."""
    email_service = MagicMock(spec=EmailService)
    email_service.send_email = AsyncMock(return_value=True)
    renderer = MagicMock(spec=TemplateRenderer)
    renderer.render.return_value = "<html>test</html>"
    handlers = NotificationHandlers(email_service, renderer)
    return handlers, email_service, renderer


def _make_adoption_event(
    aggregate_id: UUID | None = None,
    old_status: str = "pending",
    new_status: str = "approved",
) -> DomainEvent:
    """Create an adoption status changed event."""
    return DomainEvent(
        event_type=EventType.ADOPTION_STATUS_CHANGED,
        payload={"old_status": old_status, "new_status": new_status},
        aggregate_id=aggregate_id or uuid4(),
    )


def _make_donation_event(
    aggregate_id: UUID | None = None,
    amount: str = "50.00",
    currency: str = "EUR",
) -> DomainEvent:
    """Create a donation received event."""
    return DomainEvent(
        event_type=EventType.DONATION_RECEIVED,
        payload={"amount": amount, "currency": currency},
        aggregate_id=aggregate_id or uuid4(),
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class TestHandlerRegistration:
    """Verify handlers are registered on the event bus."""

    def test_register_subscribes_adoption_handler(self) -> None:
        handlers, _, _ = _make_handlers()
        bus = EventBus()
        handlers.register(bus)
        adoption_handlers = bus.get_handlers(EventType.ADOPTION_STATUS_CHANGED)
        assert len(adoption_handlers) == 1

    def test_register_subscribes_donation_handler(self) -> None:
        handlers, _, _ = _make_handlers()
        bus = EventBus()
        handlers.register(bus)
        donation_handlers = bus.get_handlers(EventType.DONATION_RECEIVED)
        assert len(donation_handlers) == 1


# ---------------------------------------------------------------------------
# Adoption Status Changed Handler
# ---------------------------------------------------------------------------
class TestAdoptionStatusChangedHandler:
    """Test on_adoption_status_changed handler."""

    @pytest.mark.asyncio
    async def test_sends_email_on_valid_event(self) -> None:
        handlers, email_service, _renderer = _make_handlers()
        event = _make_adoption_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_adoption_context",
            new_callable=AsyncMock,
            return_value=("adopter@test.com", "Maria Garcia", "Luna"),
        ):
            await handlers.on_adoption_status_changed(event)

        email_service.send_email.assert_called_once()
        call_args = email_service.send_email.call_args[0][0]
        assert call_args.to == "adopter@test.com"
        assert "Approved" in call_args.subject

    @pytest.mark.asyncio
    async def test_renders_correct_template(self) -> None:
        handlers, _, renderer = _make_handlers()
        event = _make_adoption_event(old_status="pending", new_status="rejected")

        with patch.object(
            NotificationHandlers,
            "_lookup_adoption_context",
            new_callable=AsyncMock,
            return_value=("adopter@test.com", "Maria", "Luna"),
        ):
            await handlers.on_adoption_status_changed(event)

        renderer.render.assert_called_once_with(
            "adoption_status_changed",
            {
                "adopter_name": "Maria",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "rejected",
                "staff_notes": None,
            },
        )

    @pytest.mark.asyncio
    async def test_skips_when_no_aggregate_id(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = DomainEvent(
            event_type=EventType.ADOPTION_STATUS_CHANGED,
            payload={"old_status": "pending", "new_status": "approved"},
            aggregate_id=None,
        )
        await handlers.on_adoption_status_changed(event)
        email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_adopter_email_not_found(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = _make_adoption_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_adoption_context",
            new_callable=AsyncMock,
            return_value=(None, None, None),
        ):
            await handlers.on_adoption_status_changed(event)

        email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers, _, _ = _make_handlers()
        event = _make_adoption_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_adoption_context",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB exploded"),
        ):
            # Should not raise
            await handlers.on_adoption_status_changed(event)


# ---------------------------------------------------------------------------
# Donation Received Handler
# ---------------------------------------------------------------------------
class TestDonationReceivedHandler:
    """Test on_donation_received handler."""

    @pytest.mark.asyncio
    async def test_sends_email_on_valid_event(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = _make_donation_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_donation_context",
            new_callable=AsyncMock,
            return_value=("donor@test.com", "Jan de Vries", "50.00", "EUR", "RCP-001"),
        ):
            await handlers.on_donation_received(event)

        email_service.send_email.assert_called_once()
        call_args = email_service.send_email.call_args[0][0]
        assert call_args.to == "donor@test.com"
        assert "Donation" in call_args.subject

    @pytest.mark.asyncio
    async def test_skips_when_no_aggregate_id(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            payload={"amount": "50.00", "currency": "EUR"},
            aggregate_id=None,
        )
        await handlers.on_donation_received(event)
        email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_donor_email_not_found(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = _make_donation_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_donation_context",
            new_callable=AsyncMock,
            return_value=(None, None, None, None, None),
        ):
            await handlers.on_donation_received(event)

        email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers, _, _ = _make_handlers()
        event = _make_donation_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_donation_context",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB exploded"),
        ):
            await handlers.on_donation_received(event)


# ---------------------------------------------------------------------------
# End-to-End with EventBus (unit level)
# ---------------------------------------------------------------------------
class TestHandlersWithEventBus:
    """Verify handlers fire when events are published through the bus."""

    @pytest.mark.asyncio
    async def test_adoption_event_triggers_handler_via_bus(self) -> None:
        handlers, email_service, _ = _make_handlers()
        bus = EventBus()
        handlers.register(bus)
        await bus.start()

        event = _make_adoption_event()
        with patch.object(
            NotificationHandlers,
            "_lookup_adoption_context",
            new_callable=AsyncMock,
            return_value=("adopter@test.com", "Maria", "Luna"),
        ):
            await bus.publish(event)
            await asyncio.sleep(0.2)

        await bus.stop()
        email_service.send_email.assert_called_once()
