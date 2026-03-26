"""Unit tests for the EventBus async event dispatcher."""

import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.fixture
def sample_event() -> DomainEvent:
    return DomainEvent(
        event_type=EventType.ADOPTION_STATUS_CHANGED,
        payload={"old_status": "pending", "new_status": "approved"},
        aggregate_id=uuid4(),
    )


class TestSubscription:
    """Subscribe and unsubscribe mechanics."""

    def test_subscribe_adds_handler(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.subscribe(EventType.ADOPTION_STATUS_CHANGED, handler)
        assert bus.subscriber_count == 1
        assert handler in bus.get_handlers(EventType.ADOPTION_STATUS_CHANGED)

    def test_subscribe_multiple_handlers(self, bus: EventBus) -> None:
        handler_a = AsyncMock()
        handler_b = AsyncMock()
        bus.subscribe(EventType.DONATION_RECEIVED, handler_a)
        bus.subscribe(EventType.DONATION_RECEIVED, handler_b)
        assert bus.subscriber_count == 2

    def test_subscribe_with_string_event_type(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.subscribe("adoption.status_changed", handler)
        assert handler in bus.get_handlers("adoption.status_changed")

    def test_unsubscribe_removes_handler(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.subscribe(EventType.DONATION_RECEIVED, handler)
        bus.unsubscribe(EventType.DONATION_RECEIVED, handler)
        assert bus.subscriber_count == 0

    def test_unsubscribe_nonexistent_handler_is_noop(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.unsubscribe(EventType.DONATION_RECEIVED, handler)
        assert bus.subscriber_count == 0

    def test_get_handlers_returns_copy(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.subscribe(EventType.DONATION_RECEIVED, handler)
        handlers = bus.get_handlers(EventType.DONATION_RECEIVED)
        handlers.clear()
        assert bus.subscriber_count == 1  # original not affected

    def test_get_handlers_empty_for_unknown_type(self, bus: EventBus) -> None:
        assert bus.get_handlers(EventType.ANIMAL_STATUS_CHANGED) == []


class TestPublish:
    """Publish and delivery mechanics."""

    @pytest.mark.asyncio
    async def test_publish_requires_running_bus(
        self, bus: EventBus, sample_event: DomainEvent
    ) -> None:
        with pytest.raises(RuntimeError, match="not running"):
            await bus.publish(sample_event)

    @pytest.mark.asyncio
    async def test_publish_delivers_to_subscriber(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.subscribe(EventType.ADOPTION_STATUS_CHANGED, handler)
        await bus.start()

        event = DomainEvent(
            event_type=EventType.ADOPTION_STATUS_CHANGED,
            payload={"test": True},
        )
        await bus.publish(event)

        # Give consumer task time to process
        await asyncio.sleep(0.1)
        await bus.stop()

        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_delivers_to_multiple_subscribers(
        self, bus: EventBus
    ) -> None:
        handler_a = AsyncMock()
        handler_b = AsyncMock()
        bus.subscribe(EventType.DONATION_RECEIVED, handler_a)
        bus.subscribe(EventType.DONATION_RECEIVED, handler_b)
        await bus.start()

        event = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            payload={"amount": "100"},
        )
        await bus.publish(event)
        await asyncio.sleep(0.1)
        await bus.stop()

        handler_a.assert_called_once_with(event)
        handler_b.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_publish_skips_event_with_no_subscribers(
        self, bus: EventBus
    ) -> None:
        await bus.start()
        event = DomainEvent(
            event_type=EventType.ANIMAL_STATUS_CHANGED,
            payload={},
        )
        # Should not raise, just skip silently
        await bus.publish(event)
        await bus.stop()

    @pytest.mark.asyncio
    async def test_events_routed_to_correct_handlers(self, bus: EventBus) -> None:
        adoption_handler = AsyncMock()
        donation_handler = AsyncMock()
        bus.subscribe(EventType.ADOPTION_STATUS_CHANGED, adoption_handler)
        bus.subscribe(EventType.DONATION_RECEIVED, donation_handler)
        await bus.start()

        adoption_event = DomainEvent(
            event_type=EventType.ADOPTION_STATUS_CHANGED,
            payload={"status": "approved"},
        )
        await bus.publish(adoption_event)
        await asyncio.sleep(0.1)
        await bus.stop()

        adoption_handler.assert_called_once_with(adoption_event)
        donation_handler.assert_not_called()


class TestIdempotency:
    """Duplicate event suppression via idempotency_key."""

    @pytest.mark.asyncio
    async def test_duplicate_idempotency_key_is_skipped(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.subscribe(EventType.ADOPTION_STATUS_CHANGED, handler)
        await bus.start()

        idem_key = uuid4()
        event_a = DomainEvent(
            event_type=EventType.ADOPTION_STATUS_CHANGED,
            idempotency_key=idem_key,
            payload={"attempt": 1},
        )
        event_b = DomainEvent(
            event_type=EventType.ADOPTION_STATUS_CHANGED,
            idempotency_key=idem_key,
            payload={"attempt": 2},
        )

        await bus.publish(event_a)
        await bus.publish(event_b)
        await asyncio.sleep(0.1)
        await bus.stop()

        handler.assert_called_once_with(event_a)

    @pytest.mark.asyncio
    async def test_different_idempotency_keys_both_processed(
        self, bus: EventBus
    ) -> None:
        handler = AsyncMock()
        bus.subscribe(EventType.DONATION_RECEIVED, handler)
        await bus.start()

        event_a = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            payload={"first": True},
        )
        event_b = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            payload={"second": True},
        )

        await bus.publish(event_a)
        await bus.publish(event_b)
        await asyncio.sleep(0.1)
        await bus.stop()

        assert handler.call_count == 2


class TestErrorIsolation:
    """One failing handler must not block others."""

    @pytest.mark.asyncio
    async def test_failing_handler_does_not_block_others(self, bus: EventBus) -> None:
        failing_handler = AsyncMock(side_effect=ValueError("boom"))
        healthy_handler = AsyncMock()

        bus.subscribe(EventType.MEDICAL_ALERT_CREATED, failing_handler)
        bus.subscribe(EventType.MEDICAL_ALERT_CREATED, healthy_handler)
        await bus.start()

        event = DomainEvent(
            event_type=EventType.MEDICAL_ALERT_CREATED,
            payload={"severity": "critical"},
        )
        await bus.publish(event)
        await asyncio.sleep(0.1)
        await bus.stop()

        failing_handler.assert_called_once_with(event)
        healthy_handler.assert_called_once_with(event)


class TestLifecycle:
    """Start/stop and is_running state."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self, bus: EventBus) -> None:
        assert not bus.is_running
        await bus.start()
        assert bus.is_running
        await bus.stop()

    @pytest.mark.asyncio
    async def test_stop_sets_not_running(self, bus: EventBus) -> None:
        await bus.start()
        await bus.stop()
        assert not bus.is_running

    @pytest.mark.asyncio
    async def test_start_is_idempotent(self, bus: EventBus) -> None:
        await bus.start()
        await bus.start()  # second call is no-op
        assert bus.is_running
        await bus.stop()

    @pytest.mark.asyncio
    async def test_stop_is_idempotent(self, bus: EventBus) -> None:
        await bus.start()
        await bus.stop()
        await bus.stop()  # second call is no-op
        assert not bus.is_running

    @pytest.mark.asyncio
    async def test_stop_drains_queued_events(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.subscribe(EventType.VOLUNTEER_SHIFT_CREATED, handler)
        await bus.start()

        for i in range(5):
            await bus.publish(
                DomainEvent(
                    event_type=EventType.VOLUNTEER_SHIFT_CREATED,
                    payload={"index": i},
                )
            )

        await bus.stop()
        assert handler.call_count == 5

    @pytest.mark.asyncio
    async def test_start_clears_processed_keys(self, bus: EventBus) -> None:
        handler = AsyncMock()
        bus.subscribe(EventType.DONATION_RECEIVED, handler)

        idem_key = uuid4()
        event = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            idempotency_key=idem_key,
            payload={},
        )

        # First run
        await bus.start()
        await bus.publish(event)
        await asyncio.sleep(0.1)
        await bus.stop()
        assert handler.call_count == 1

        # Second run — same key should be processed again after restart
        await bus.start()
        await bus.publish(event)
        await asyncio.sleep(0.1)
        await bus.stop()
        assert handler.call_count == 2
