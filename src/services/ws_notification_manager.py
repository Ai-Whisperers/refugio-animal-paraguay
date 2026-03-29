"""WebSocket connection manager for real-time in-app notifications.

Manages active WebSocket connections per user. When a new notification
is dispatched via the EventBus, the handler calls broadcast_to_user()
to push the payload to all of that user's open WebSocket connections.

Architecture:
    EventBus → WSNotificationHandler → WSNotificationManager → WS clients

Thread safety: asyncio.Lock guards the connections dict for safe
concurrent access. All operations are awaited.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from fastapi import WebSocket
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

# Maximum concurrent WebSocket connections across all users
MAX_WS_CONNECTIONS = 500


@dataclass
class WSConnection:
    """A single authenticated WebSocket connection."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    websocket: WebSocket = field(default=None)  # type: ignore[assignment]

    def is_open(self) -> bool:
        """Return True if the WebSocket is still connected."""
        return self.websocket.client_state == WebSocketState.CONNECTED


class WSNotificationManager:
    """Manages per-user WebSocket connections for real-time notifications.

    Connections are stored as:
        _connections: dict[user_id, list[WSConnection]]

    Multiple browser tabs for the same user each get their own connection
    and all receive the same broadcasts.
    """

    def __init__(self) -> None:
        self._connections: dict[UUID, list[WSConnection]] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: UUID) -> WSConnection:
        """Accept the WebSocket and register the connection."""
        total = sum(len(conns) for conns in self._connections.values())
        if total >= MAX_WS_CONNECTIONS:
            await websocket.close(code=1013, reason="Too many connections")
            raise ConnectionError("Max WebSocket connections reached")

        await websocket.accept()
        connection = WSConnection(user_id=user_id, websocket=websocket)

        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = []
            self._connections[user_id].append(connection)

        logger.info(
            "WS notification connection opened: user=%s conn=%s",
            user_id,
            connection.id,
        )
        return connection

    async def disconnect(self, connection: WSConnection) -> None:
        """Remove the connection from the registry."""
        async with self._lock:
            user_conns = self._connections.get(connection.user_id, [])
            self._connections[connection.user_id] = [
                c for c in user_conns if c.id != connection.id
            ]
            if not self._connections[connection.user_id]:
                del self._connections[connection.user_id]

        logger.info(
            "WS notification connection closed: user=%s conn=%s",
            connection.user_id,
            connection.id,
        )

    async def broadcast_to_user(self, user_id: UUID, payload: dict) -> None:
        """Send a JSON payload to all connections for *user_id*."""
        async with self._lock:
            user_conns = list(self._connections.get(user_id, []))

        if not user_conns:
            return

        message = json.dumps(payload)
        dead: list[WSConnection] = []

        for conn in user_conns:
            if not conn.is_open():
                dead.append(conn)
                continue
            try:
                await conn.websocket.send_text(message)
            except Exception:
                logger.debug("WS send failed for conn %s — marking dead", conn.id)
                dead.append(conn)

        # Clean up dead connections
        for conn in dead:
            await self.disconnect(conn)

    async def broadcast_to_all(self, payload: dict) -> None:
        """Send a JSON payload to ALL connected users (admin broadcasts)."""
        async with self._lock:
            all_user_ids = list(self._connections.keys())

        for user_id in all_user_ids:
            await self.broadcast_to_user(user_id, payload)

    @property
    def connection_count(self) -> int:
        return sum(len(c) for c in self._connections.values())


# Singleton used throughout the application
ws_notification_manager = WSNotificationManager()
