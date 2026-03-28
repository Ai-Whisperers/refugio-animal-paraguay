"""Unit tests for SSE connection manager and message formatting."""

import asyncio
from uuid import uuid4

import pytest
from src.services.sse_service import (
    HEARTBEAT_INTERVAL_SECONDS,
    MAX_QUEUE_SIZE_PER_CONNECTION,
    MAX_SSE_CONNECTIONS,
    SSEConnection,
    SSEConnectionManager,
    SSEMessage,
)

# ---------------------------------------------------------------------------
# SSEMessage tests
# ---------------------------------------------------------------------------


class TestSSEMessage:
    """Tests for SSE message formatting."""

    def test_basic_format(self) -> None:
        msg = SSEMessage(event="test", data="hello", id="123")
        formatted = msg.format()
        assert "id: 123" in formatted
        assert "event: test" in formatted
        assert "data: hello" in formatted

    def test_multiline_data(self) -> None:
        msg = SSEMessage(event="test", data="line1\nline2\nline3", id="456")
        formatted = msg.format()
        assert "data: line1" in formatted
        assert "data: line2" in formatted
        assert "data: line3" in formatted

    def test_retry_field(self) -> None:
        msg = SSEMessage(event="test", data="hello", id="789", retry=5000)
        formatted = msg.format()
        assert "retry: 5000" in formatted

    def test_no_retry_by_default(self) -> None:
        msg = SSEMessage(event="test", data="hello", id="abc")
        formatted = msg.format()
        assert "retry:" not in formatted

    def test_ends_with_double_newline(self) -> None:
        msg = SSEMessage(event="test", data="hello", id="def")
        formatted = msg.format()
        assert formatted.endswith("\n\n")

    def test_auto_generates_id(self) -> None:
        msg = SSEMessage(event="test", data="hello")
        assert msg.id  # Should have auto-generated UUID


# ---------------------------------------------------------------------------
# SSEConnection tests
# ---------------------------------------------------------------------------


class TestSSEConnection:
    """Tests for individual SSE connections."""

    @pytest.mark.asyncio
    async def test_send_queues_message(self) -> None:
        conn = SSEConnection()
        msg = SSEMessage(event="test", data="hello")
        result = await conn.send(msg)
        assert result is True
        assert conn.queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_send_returns_false_when_full(self) -> None:
        conn = SSEConnection(queue=asyncio.Queue(maxsize=1))
        msg1 = SSEMessage(event="test", data="first")
        msg2 = SSEMessage(event="test", data="second")
        await conn.send(msg1)
        result = await conn.send(msg2)
        assert result is False

    @pytest.mark.asyncio
    async def test_close_sends_none_sentinel(self) -> None:
        conn = SSEConnection()
        await conn.close()
        item = conn.queue.get_nowait()
        assert item is None

    def test_has_user_id(self) -> None:
        uid = uuid4()
        conn = SSEConnection(user_id=uid)
        assert conn.user_id == uid

    def test_has_unique_id(self) -> None:
        c1 = SSEConnection()
        c2 = SSEConnection()
        assert c1.id != c2.id


# ---------------------------------------------------------------------------
# SSEConnectionManager tests
# ---------------------------------------------------------------------------


class TestSSEConnectionManager:
    """Tests for the SSE connection manager."""

    def test_connect_returns_connection(self) -> None:
        manager = SSEConnectionManager()
        conn = manager.connect()
        assert isinstance(conn, SSEConnection)
        assert manager.connection_count == 1

    def test_disconnect_removes_connection(self) -> None:
        manager = SSEConnectionManager()
        conn = manager.connect()
        manager.disconnect(conn.id)
        assert manager.connection_count == 0

    def test_disconnect_nonexistent_is_noop(self) -> None:
        manager = SSEConnectionManager()
        manager.disconnect(uuid4())
        assert manager.connection_count == 0

    def test_max_connections_enforced(self) -> None:
        manager = SSEConnectionManager(max_connections=2)
        manager.connect()
        manager.connect()
        with pytest.raises(ConnectionError, match="Maximum SSE connections"):
            manager.connect()

    @pytest.mark.asyncio
    async def test_broadcast_delivers_to_all(self) -> None:
        manager = SSEConnectionManager()
        c1 = manager.connect()
        c2 = manager.connect()
        msg = SSEMessage(event="test", data="broadcast")
        delivered = await manager.broadcast(msg)
        assert delivered == 2
        assert c1.queue.qsize() == 1
        assert c2.queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_broadcast_with_no_connections(self) -> None:
        manager = SSEConnectionManager()
        msg = SSEMessage(event="test", data="nobody")
        delivered = await manager.broadcast(msg)
        assert delivered == 0

    @pytest.mark.asyncio
    async def test_send_to_user(self) -> None:
        manager = SSEConnectionManager()
        user1 = uuid4()
        user2 = uuid4()
        c1 = manager.connect(user_id=user1)
        manager.connect(user_id=user2)
        msg = SSEMessage(event="test", data="user-specific")
        delivered = await manager.send_to_user(user1, msg)
        assert delivered == 1
        assert c1.queue.qsize() == 1


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify SSE service constants."""

    def test_max_connections(self) -> None:
        assert MAX_SSE_CONNECTIONS == 100

    def test_heartbeat_interval(self) -> None:
        assert HEARTBEAT_INTERVAL_SECONDS == 30

    def test_max_queue_size(self) -> None:
        assert MAX_QUEUE_SIZE_PER_CONNECTION == 50
