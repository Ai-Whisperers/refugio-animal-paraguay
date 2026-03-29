"""Unit tests for WSNotificationManager.

Tests the connection management logic without real WebSocket connections.
"""

from __future__ import annotations

import json
from uuid import UUID, uuid4

import pytest
from src.services.ws_notification_manager import WSNotificationManager


class MockWebSocket:
    """Minimal WebSocket mock for testing."""

    def __init__(self, state: str = "CONNECTED") -> None:
        self._state = state
        self.sent_messages: list[str] = []
        self.close_calls: list[tuple] = []

    @property
    def client_state(self) -> object:
        from starlette.websockets import WebSocketState
        return WebSocketState.CONNECTED if self._state == "CONNECTED" else WebSocketState.DISCONNECTED

    async def accept(self) -> None:
        pass

    async def send_text(self, data: str) -> None:
        self.sent_messages.append(data)

    async def close(self, code: int = 1000, reason: str = "") -> None:
        self.close_calls.append((code, reason))
        self._state = "DISCONNECTED"


@pytest.fixture()
def manager() -> WSNotificationManager:
    return WSNotificationManager()


@pytest.fixture()
def mock_ws() -> MockWebSocket:
    return MockWebSocket()


@pytest.fixture()
def user_id() -> UUID:
    return uuid4()


class TestWSNotificationManager:
    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(
        self, manager: WSNotificationManager, mock_ws: MockWebSocket, user_id: UUID
    ) -> None:
        conn = await manager.connect(mock_ws, user_id)  # type: ignore[arg-type]
        assert conn.user_id == user_id
        assert manager.connection_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(
        self, manager: WSNotificationManager, mock_ws: MockWebSocket, user_id: UUID
    ) -> None:
        conn = await manager.connect(mock_ws, user_id)  # type: ignore[arg-type]
        await manager.disconnect(conn)
        assert manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_json_to_user(
        self, manager: WSNotificationManager, mock_ws: MockWebSocket, user_id: UUID
    ) -> None:
        await manager.connect(mock_ws, user_id)  # type: ignore[arg-type]
        payload = {"event": "notification", "data": {"title": "Test"}}
        await manager.broadcast_to_user(user_id, payload)
        assert len(mock_ws.sent_messages) == 1
        received = json.loads(mock_ws.sent_messages[0])
        assert received["event"] == "notification"
        assert received["data"]["title"] == "Test"

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_user_is_no_op(
        self, manager: WSNotificationManager
    ) -> None:
        await manager.broadcast_to_user(uuid4(), {"event": "notification"})
        # No exception raised

    @pytest.mark.asyncio
    async def test_multiple_connections_same_user_both_receive(
        self, manager: WSNotificationManager, user_id: UUID
    ) -> None:
        ws1, ws2 = MockWebSocket(), MockWebSocket()
        await manager.connect(ws1, user_id)  # type: ignore[arg-type]
        await manager.connect(ws2, user_id)  # type: ignore[arg-type]
        assert manager.connection_count == 2

        await manager.broadcast_to_user(user_id, {"event": "ping"})
        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_broadcast_to_all_reaches_all_users(
        self, manager: WSNotificationManager
    ) -> None:
        user_a, user_b = uuid4(), uuid4()
        ws_a, ws_b = MockWebSocket(), MockWebSocket()
        await manager.connect(ws_a, user_a)  # type: ignore[arg-type]
        await manager.connect(ws_b, user_b)  # type: ignore[arg-type]

        payload = {"event": "notification", "data": {"title": "Global"}}
        await manager.broadcast_to_all(payload)

        assert len(ws_a.sent_messages) == 1
        assert len(ws_b.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up_empty_user_entry(
        self, manager: WSNotificationManager, mock_ws: MockWebSocket, user_id: UUID
    ) -> None:
        conn = await manager.connect(mock_ws, user_id)  # type: ignore[arg-type]
        await manager.disconnect(conn)
        # User entry should be removed entirely (not left as empty list)
        assert user_id not in manager._connections
