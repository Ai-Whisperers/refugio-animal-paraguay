"""Unit tests for the event bus infrastructure."""

import asyncio
from datetime import UTC
from unittest.mock import AsyncMock

import pytest
from src.events.base import DomainEvent, EventBus
from src.events.domain_events import (
    AdoptionStatusChanged,
    AnimalIntake,
    DonationReceived,
    MedicalAlert,
    VolunteerShiftCreated,
)


class TestDomainEvent:
    """Tests for the base DomainEvent dataclass."""

    def test_default_fields_populated(self) -> None:
        event = DomainEvent(event_type="test.event")
        assert event.event_type == "test.event"
        assert event.payload == {}
        assert event.timestamp.tzinfo is not None
        assert event.actor_id is None
        assert len(event.idempotency_key) > 0

    def test_custom_payload(self) -> None:
        event = DomainEvent(
            event_type="test.event",
            payload={"animal_id": "abc-123", "status": "adopted"},
            actor_id="user-456",
        )
        assert event.payload["animal_id"] == "abc-123"
        assert event.actor_id == "user-456"

    def test_unique_idempotency_keys(self) -> None:
        events = [DomainEvent(event_type="test") for _ in range(100)]
        keys = {e.idempotency_key for e in events}
        assert len(keys) == 100

    def test_frozen_immutable(self) -> None:
        event = DomainEvent(event_type="test")
        with pytest.raises(AttributeError):
            event.event_type = "changed"  # type: ignore[misc]

    def test_timestamp_is_utc(self) -> None:
        event = DomainEvent(event_type="test")
        assert event.timestamp.tzinfo == UTC


class TestConcreteEvents:
    """Tests for concrete domain event classes."""

    def test_adoption_status_changed_event_type(self) -> None:
        event = AdoptionStatusChanged(
            payload={
                "adoption_request_id": "123",
                "old_status": "pending",
                "new_status": "approved",
            }
        )
        assert event.event_type == "adoption.status_changed"

    def test_donation_received_event_type(self) -> None:
        event = DonationReceived(
            payload={"donation_id": "456", "amount_cents": 5000, "currency": "EUR"}
        )
        assert event.event_type == "donation.received"

    def test_medical_alert_event_type(self) -> None:
        event = MedicalAlert(payload={"animal_id": "789", "alert_type": "vaccination_overdue"})
        assert event.event_type == "medical.alert"

    def test_volunteer_shift_created_event_type(self) -> None:
        event = VolunteerShiftCreated(payload={"shift_id": "101", "volunteer_id": "202"})
        assert event.event_type == "volunteer.shift_created"

    def test_animal_intake_event_type(self) -> None:
        event = AnimalIntake(payload={"animal_id": "303", "species": "dog", "name": "Luna"})
        assert event.event_type == "animal.intake"

    def test_concrete_events_carry_actor_id(self) -> None:
        event = DonationReceived(
            payload={"donation_id": "x"},
            actor_id="admin-user",
        )
        assert event.actor_id == "admin-user"


class TestEventBus:
    """Tests for the EventBus publish/subscribe mechanics."""

    @pytest.fixture
    def bus(self) -> EventBus:
        return EventBus(max_retries=2)

    @pytest.mark.asyncio
    async def test_handler_receives_published_event(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.subscribe("test.event", handler)

        event = DomainEvent(event_type="test.event", payload={"key": "value"})
        await bus.publish(event)

        handler.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_multiple_handlers_all_called(self, bus: EventBus) -> None:
        handler_a = AsyncMock()
        handler_b = AsyncMock()
        handler_c = AsyncMock()
        bus.subscribe("test.event", handler_a)
        bus.subscribe("test.event", handler_b)
        bus.subscribe("test.event", handler_c)

        event = DomainEvent(event_type="test.event")
        await bus.publish(event)

        handler_a.assert_awaited_once_with(event)
        handler_b.assert_awaited_once_with(event)
        handler_c.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_handler_only_called_for_subscribed_type(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.subscribe("type_a", handler)

        event = DomainEvent(event_type="type_b")
        await bus.publish(event)

        handler.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_handlers_does_not_raise(self, bus: EventBus) -> None:
        event = DomainEvent(event_type="orphan.event")
        await bus.publish(event)  # Should not raise

    @pytest.mark.asyncio
    async def test_error_isolation_other_handlers_still_called(self, bus: EventBus) -> None:
        failing_handler = AsyncMock(side_effect=RuntimeError("boom"))
        success_handler = AsyncMock()

        bus.subscribe("test.event", failing_handler)
        bus.subscribe("test.event", success_handler)

        event = DomainEvent(event_type="test.event")
        await bus.publish(event)

        # Success handler should still be called despite failure
        success_handler.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_handler_retried_on_failure(self, bus: EventBus) -> None:
        handler = AsyncMock(side_effect=[RuntimeError("fail"), None])
        bus.subscribe("test.event", handler)

        event = DomainEvent(event_type="test.event")
        await bus.publish(event)

        assert handler.await_count == 2

    @pytest.mark.asyncio
    async def test_handler_max_retries_exhausted(self, bus: EventBus) -> None:
        handler = AsyncMock(side_effect=RuntimeError("always fails"))
        bus.subscribe("test.event", handler)

        event = DomainEvent(event_type="test.event")
        await bus.publish(event)

        # Should be called max_retries times (2)
        assert handler.await_count == 2

    def test_unsubscribe_removes_handler(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.subscribe("test.event", handler)
        assert bus.handler_count == 1

        bus.unsubscribe("test.event", handler)
        assert bus.handler_count == 0

    def test_unsubscribe_nonexistent_handler_no_error(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.unsubscribe("test.event", handler)  # Should not raise

    def test_clear_removes_all_handlers(self, bus: EventBus) -> None:
        bus.subscribe("type_a", AsyncMock())
        bus.subscribe("type_b", AsyncMock())
        bus.subscribe("type_b", AsyncMock())
        assert bus.handler_count == 3

        bus.clear()
        assert bus.handler_count == 0

    def test_handler_count(self, bus: EventBus) -> None:
        assert bus.handler_count == 0
        bus.subscribe("a", AsyncMock())
        assert bus.handler_count == 1
        bus.subscribe("b", AsyncMock())
        assert bus.handler_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_handlers_execute_in_parallel(self, bus: EventBus) -> None:
        """Handlers should execute concurrently, not sequentially."""
        call_order: list[str] = []

        async def slow_handler(event: DomainEvent) -> None:
            call_order.append("slow_start")
            await asyncio.sleep(0.05)
            call_order.append("slow_end")

        async def fast_handler(event: DomainEvent) -> None:
            call_order.append("fast_start")
            call_order.append("fast_end")

        bus.subscribe("test", slow_handler)
        bus.subscribe("test", fast_handler)

        await bus.publish(DomainEvent(event_type="test"))

        # Fast handler should start before slow handler finishes
        assert "fast_start" in call_order
        assert "fast_end" in call_order
        assert "slow_start" in call_order
        assert "slow_end" in call_order
