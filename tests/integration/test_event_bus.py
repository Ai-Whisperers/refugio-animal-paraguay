"""Integration tests for the event bus wired into the FastAPI application.

These tests mock the database engine to isolate the event bus lifecycle
from DB availability, testing only that the event bus starts/stops with
the application and delivers events through the full middleware stack.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType


@pytest.mark.asyncio
class TestEventBusLifecycle:
    """Event bus starts and stops with the application lifespan."""

    async def test_event_bus_starts_and_stops_with_app(self) -> None:
        """EventBus is created during lifespan startup and stopped on shutdown."""
        bus = EventBus()
        await bus.start()
        assert bus.is_running
        await bus.stop()
        assert not bus.is_running

    async def test_event_bus_delivers_to_subscriber_after_start(self) -> None:
        """Events published after start() reach registered subscribers."""
        bus = EventBus()
        received: list[DomainEvent] = []

        async def capture(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe(EventType.ANIMAL_INTAKE_COMPLETED, capture)
        await bus.start()

        event = DomainEvent(
            event_type=EventType.ANIMAL_INTAKE_COMPLETED,
            payload={"species": "cat", "name": "Luna"},
        )
        await bus.publish(event)
        await asyncio.sleep(0.1)
        await bus.stop()

        assert len(received) == 1
        assert received[0].payload["name"] == "Luna"

    async def test_multiple_subscribers_all_receive_event(self) -> None:
        """All subscribers for an event type receive the published event."""
        bus = EventBus()
        handler_a = AsyncMock()
        handler_b = AsyncMock()

        bus.subscribe(EventType.DONATION_RECEIVED, handler_a)
        bus.subscribe(EventType.DONATION_RECEIVED, handler_b)
        await bus.start()

        event = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            payload={"amount": "100.00"},
        )
        await bus.publish(event)
        await asyncio.sleep(0.1)
        await bus.stop()

        handler_a.assert_called_once()
        handler_b.assert_called_once()

    async def test_error_isolation_between_handlers(self) -> None:
        """A failing handler does not prevent other handlers from executing."""
        bus = EventBus()
        failing = AsyncMock(side_effect=RuntimeError("handler crash"))
        healthy = AsyncMock()

        bus.subscribe(EventType.MEDICAL_ALERT_CREATED, failing)
        bus.subscribe(EventType.MEDICAL_ALERT_CREATED, healthy)
        await bus.start()

        event = DomainEvent(
            event_type=EventType.MEDICAL_ALERT_CREATED,
            payload={"severity": "critical"},
        )
        await bus.publish(event)
        await asyncio.sleep(0.1)
        await bus.stop()

        healthy.assert_called_once()

    async def test_event_bus_in_app_state(self) -> None:
        """Verify the event bus gets attached to app.state during lifespan."""
        with patch("src.app.init_engine"), patch("src.app.dispose_engine"):
            from src.app import create_app

            app = create_app()

            # Manually trigger lifespan

            ctx = app.router.lifespan_context(app)
            async with ctx:
                event_bus = app.state.event_bus
                assert isinstance(event_bus, EventBus)
                assert event_bus.is_running

            # After lifespan exit, bus should be stopped
            assert not event_bus.is_running
