"""Unit tests for event bus FastAPI dependency."""

from unittest.mock import MagicMock

import pytest
from fastapi import Request
from src.events.bus import EventBus
from src.events.dependencies import get_event_bus


def _make_request(event_bus: EventBus | None = None) -> Request:
    """Create a mock Request with optional event_bus on app.state."""
    request = MagicMock(spec=Request)
    state = MagicMock()
    if event_bus is not None:
        state.event_bus = event_bus
    else:
        # Simulate missing attribute
        del state.event_bus
        type(state).event_bus = property(lambda self: (_ for _ in ()).throw(AttributeError))
    app = MagicMock()
    app.state = state
    request.app = app
    return request


class TestGetEventBus:
    """Tests for the get_event_bus dependency."""

    def test_returns_event_bus_from_state(self) -> None:
        bus = EventBus()
        request = _make_request(event_bus=bus)
        result = get_event_bus(request)
        assert result is bus

    def test_raises_when_event_bus_missing(self) -> None:
        request = _make_request(event_bus=None)
        with pytest.raises(RuntimeError, match="EventBus not available"):
            get_event_bus(request)
