"""Server-Sent Events (SSE) connection manager.

Manages active SSE connections for real-time admin notifications.
Event handlers push messages to connected clients via the manager.

Architecture:
    EventBus -> DonationSSEHandler -> SSEConnectionManager -> Client streams

Thread safety: uses asyncio.Queue per connection, safe for concurrent access.
"""

import asyncio
import contextlib
import logging
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

# Maximum number of concurrent SSE connections
MAX_SSE_CONNECTIONS = 100

# Heartbeat interval in seconds (keeps connections alive through proxies)
HEARTBEAT_INTERVAL_SECONDS = 30

# Maximum events queued per connection before dropping old events
MAX_QUEUE_SIZE_PER_CONNECTION = 50


@dataclass
class SSEMessage:
    """A single SSE message to send to connected clients."""

    event: str
    data: str
    id: str = field(default_factory=lambda: str(uuid4()))
    retry: int | None = None

    def format(self) -> str:
        """Format as SSE wire protocol."""
        lines = []
        if self.id:
            lines.append(f"id: {self.id}")
        lines.append(f"event: {self.event}")
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        for line in self.data.split("\n"):
            lines.append(f"data: {line}")
        lines.append("")
        lines.append("")
        return "\n".join(lines)


@dataclass
class SSEConnection:
    """Represents a single SSE client connection."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    queue: asyncio.Queue[SSEMessage | None] = field(
        default_factory=lambda: asyncio.Queue(maxsize=MAX_QUEUE_SIZE_PER_CONNECTION)
    )
    connected_at: float = field(default_factory=time.monotonic)

    async def send(self, message: SSEMessage) -> bool:
        """Queue a message for this connection. Returns False if queue is full."""
        try:
            self.queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            logger.warning(
                "SSE queue full for connection %s, dropping message",
                self.id,
            )
            return False

    async def close(self) -> None:
        """Signal this connection to close by sending None sentinel."""
        with contextlib.suppress(asyncio.QueueFull):
            self.queue.put_nowait(None)


class SSEConnectionManager:
    """Manages active SSE connections and broadcasts messages.

    Usage:
        manager = SSEConnectionManager()
        conn = manager.connect(user_id=admin_id)
        # ... stream from conn.queue ...
        manager.disconnect(conn.id)
    """

    def __init__(self, max_connections: int = MAX_SSE_CONNECTIONS) -> None:
        self._connections: dict[UUID, SSEConnection] = {}
        self._max_connections = max_connections

    def connect(self, user_id: UUID | None = None) -> SSEConnection:
        """Register a new SSE connection.

        Raises:
            ConnectionError: If max connections exceeded.
        """
        if len(self._connections) >= self._max_connections:
            raise ConnectionError(f"Maximum SSE connections ({self._max_connections}) exceeded")

        conn = SSEConnection(user_id=user_id)
        self._connections[conn.id] = conn
        logger.info(
            "SSE connection opened: %s (user=%s, total=%d)",
            conn.id,
            user_id,
            len(self._connections),
        )
        return conn

    def disconnect(self, connection_id: UUID) -> None:
        """Remove a connection from the manager."""
        conn = self._connections.pop(connection_id, None)
        if conn:
            logger.info(
                "SSE connection closed: %s (total=%d)",
                connection_id,
                len(self._connections),
            )

    async def broadcast(self, message: SSEMessage) -> int:
        """Send a message to all connected clients.

        Returns the number of clients that received the message.
        """
        if not self._connections:
            return 0

        delivered = 0
        for conn in self._connections.values():
            if await conn.send(message):
                delivered += 1

        logger.debug(
            "SSE broadcast: event=%s delivered=%d/%d",
            message.event,
            delivered,
            len(self._connections),
        )
        return delivered

    async def send_to_user(self, user_id: UUID, message: SSEMessage) -> int:
        """Send a message to all connections for a specific user."""
        delivered = 0
        for conn in self._connections.values():
            if conn.user_id == user_id and await conn.send(message):
                delivered += 1
        return delivered

    @property
    def connection_count(self) -> int:
        """Number of active SSE connections."""
        return len(self._connections)

    async def stream(self, connection: SSEConnection) -> AsyncGenerator[str, None]:
        """Generate SSE stream for a connection, including heartbeats.

        Yields formatted SSE messages. Sends periodic heartbeat comments
        to keep the connection alive through proxies/load balancers.
        """
        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        connection.queue.get(),
                        timeout=HEARTBEAT_INTERVAL_SECONDS,
                    )
                except TimeoutError:
                    # Send heartbeat comment (keeps connection alive)
                    yield ": heartbeat\n\n"
                    continue

                if message is None:
                    # Sentinel: close the stream
                    break

                yield message.format()
        finally:
            self.disconnect(connection.id)


# Module-level singleton — shared across the application
sse_manager = SSEConnectionManager()
