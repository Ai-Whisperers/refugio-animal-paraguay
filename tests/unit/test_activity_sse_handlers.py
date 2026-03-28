"""Unit tests for ActivitySSEHandlers and activity message formatting."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.events.types import DomainEvent, EventType
from src.notifications.activity_sse_handlers import (
    ActivitySSEHandlers,
    _format_activity_message,
    _get_icon_and_category,
)
from src.services.sse_service import SSEMessage

# ---- Message formatting tests ----


class TestFormatActivityMessage:
    """Tests for _format_activity_message helper."""

    def test_donation_received_message(self) -> None:
        event = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            payload={"amount": "50.00", "currency": "EUR"},
        )
        result = _format_activity_message(event)
        assert "50.00" in result
        assert "EUR" in result
        assert "donacion" in result.lower()

    def test_adoption_request_created_message(self) -> None:
        event = DomainEvent(
            event_type=EventType.ADOPTION_REQUEST_CREATED,
            payload={},
        )
        result = _format_activity_message(event)
        assert "solicitud" in result.lower()
        assert "adopcion" in result.lower()

    def test_adoption_status_changed_message(self) -> None:
        event = DomainEvent(
            event_type=EventType.ADOPTION_STATUS_CHANGED,
            payload={"old_status": "pending", "new_status": "approved"},
        )
        result = _format_activity_message(event)
        assert "pending" in result
        assert "approved" in result

    def test_animal_intake_message(self) -> None:
        event = DomainEvent(
            event_type=EventType.ANIMAL_INTAKE_COMPLETED,
            payload={"name": "Luna"},
        )
        result = _format_activity_message(event)
        assert "Luna" in result

    def test_missing_placeholder_graceful_fallback(self) -> None:
        """When payload is missing expected keys, should not raise."""
        event = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            payload={},  # missing 'amount' and 'currency'
        )
        result = _format_activity_message(event)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_subscription_cancelled_message(self) -> None:
        event = DomainEvent(
            event_type=EventType.SUBSCRIPTION_CANCELLED_DUNNING,
            payload={},
        )
        result = _format_activity_message(event)
        assert "suscripcion" in result.lower()


class TestGetIconAndCategory:
    """Tests for _get_icon_and_category helper."""

    def test_donation_category(self) -> None:
        event = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            payload={},
        )
        icon, category = _get_icon_and_category(event)
        assert category == "donation"
        assert icon == "dollar-sign"

    def test_adoption_category(self) -> None:
        event = DomainEvent(
            event_type=EventType.ADOPTION_REQUEST_CREATED,
            payload={},
        )
        icon, category = _get_icon_and_category(event)
        assert category == "adoption"
        assert icon == "heart"

    def test_medical_category(self) -> None:
        event = DomainEvent(
            event_type=EventType.MEDICAL_ALERT_CREATED,
            payload={},
        )
        _icon, category = _get_icon_and_category(event)
        assert category == "medical"

    def test_all_event_types_have_mapping(self) -> None:
        """Every EventType should return a valid icon and category."""
        for event_type in EventType:
            event = DomainEvent(event_type=event_type, payload={})
            icon, category = _get_icon_and_category(event)
            assert isinstance(icon, str)
            assert isinstance(category, str)
            assert len(icon) > 0
            assert len(category) > 0


# ---- Handler registration and broadcast tests ----


class TestActivitySSEHandlers:
    """Tests for ActivitySSEHandlers class."""

    def test_register_subscribes_to_all_event_types(self) -> None:
        mock_sse_manager = MagicMock()
        mock_bus = MagicMock()
        handlers = ActivitySSEHandlers(mock_sse_manager)

        handlers.register(mock_bus)

        # Should subscribe once per EventType
        assert mock_bus.subscribe.call_count == len(EventType)

    @pytest.mark.asyncio
    async def test_on_event_broadcasts_sse_message(self) -> None:
        mock_sse_manager = MagicMock()
        mock_sse_manager.broadcast = AsyncMock(return_value=2)

        handlers = ActivitySSEHandlers(mock_sse_manager)

        event = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            payload={"amount": "100.00", "currency": "PYG"},
            aggregate_id=uuid4(),
            aggregate_type="donation",
            actor_id=uuid4(),
            timestamp=datetime.now(UTC),
        )

        await handlers._on_event(event)

        mock_sse_manager.broadcast.assert_called_once()
        call_args = mock_sse_manager.broadcast.call_args[0][0]
        assert isinstance(call_args, SSEMessage)
        assert call_args.event == "activity"
        assert "donation" in call_args.data
        assert "100.00" in call_args.data

    @pytest.mark.asyncio
    async def test_on_event_includes_metadata(self) -> None:
        """Broadcast message should include aggregate_id, actor_id, timestamp."""
        mock_sse_manager = MagicMock()
        mock_sse_manager.broadcast = AsyncMock(return_value=1)

        handlers = ActivitySSEHandlers(mock_sse_manager)
        agg_id = uuid4()
        actor_id = uuid4()

        event = DomainEvent(
            event_type=EventType.ANIMAL_INTAKE_COMPLETED,
            payload={"name": "Rex"},
            aggregate_id=agg_id,
            actor_id=actor_id,
        )

        await handlers._on_event(event)

        call_args = mock_sse_manager.broadcast.call_args[0][0]
        assert str(agg_id) in call_args.data
        assert str(actor_id) in call_args.data
        assert "Rex" in call_args.data

    @pytest.mark.asyncio
    async def test_on_event_zero_delivered_no_error(self) -> None:
        """When no clients are connected, broadcast returns 0 — no error."""
        mock_sse_manager = MagicMock()
        mock_sse_manager.broadcast = AsyncMock(return_value=0)

        handlers = ActivitySSEHandlers(mock_sse_manager)

        event = DomainEvent(
            event_type=EventType.MEDICAL_RECORD_ADDED,
            payload={},
        )

        # Should not raise
        await handlers._on_event(event)
        mock_sse_manager.broadcast.assert_called_once()
