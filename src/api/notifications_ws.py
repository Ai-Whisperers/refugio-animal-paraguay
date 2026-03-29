"""WebSocket endpoint for real-time in-app notifications.

Provides a WebSocket connection at /ws/notifications that staff and
authenticated users can connect to for real-time notification delivery.

The client authenticates by passing a JWT token as a query parameter:
    ws://host/ws/notifications?token=<jwt>

Incoming messages from the server are JSON objects:
    {"event": "notification", "data": {...notification fields...}}
    {"event": "ping"}

The client may send "pong" to respond to server pings (keep-alive).

Security:
- Token validated on connection; connection closes on invalid/expired token
- Only staff and admin roles can connect
"""

from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError

from src.auth.utils import decode_access_token
from src.config import get_settings
from src.db.models.user import User, UserRole
from src.db.session import get_async_session
from src.services.ws_notification_manager import ws_notification_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["notifications-ws"])

# Ping interval (seconds) — keeps connections alive through proxies/load balancers
PING_INTERVAL_SECONDS = 25


async def _authenticate_ws(token: str) -> User | None:
    """Authenticate the WebSocket token and return the User or None.

    Returns None if the token is invalid, expired, the user is inactive,
    or the user does not have staff/admin role.
    """
    settings = get_settings()
    try:
        payload = decode_access_token(token, settings.secret_key, settings.algorithm)
        user_id_str: str | None = payload.get("sub")  # type: ignore[assignment]
        if not user_id_str:
            return None
    except JWTError:
        return None

    async with get_async_session() as db:
        user = await db.get(User, user_id_str)

    if user is None or not user.is_active:
        return None

    if user.role not in (UserRole.STAFF.value, UserRole.ADMIN.value):
        return None

    return user


@router.websocket("/ws/notifications")
async def ws_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="JWT bearer token"),
) -> None:
    """WebSocket endpoint for real-time in-app notifications.

    Connect with:
        ws://host/ws/notifications?token=<jwt>

    The server sends JSON messages:
        {"event": "notification", "data": {...}}
        {"event": "ping"}

    The client should respond to "ping" with "pong" to confirm liveness.
    The connection closes when the token expires or the server restarts.
    """
    user = await _authenticate_ws(token)
    if user is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    try:
        connection = await ws_notification_manager.connect(websocket, UUID(str(user.id)))
    except ConnectionError:
        # Manager already closed the socket with 1013
        return

    logger.info("WS /notifications connected: user=%s conn=%s", user.id, connection.id)

    async def ping_loop() -> None:
        """Send periodic pings to keep the connection alive through proxies."""
        while True:
            await asyncio.sleep(PING_INTERVAL_SECONDS)
            if not connection.is_open():
                break
            try:
                await websocket.send_text(json.dumps({"event": "ping"}))
            except Exception:
                break

    ping_task = asyncio.create_task(ping_loop())

    try:
        while True:
            try:
                await websocket.receive_text()
                # Accept pong/heartbeat messages; no action needed
            except WebSocketDisconnect:
                break
            except Exception:
                break
    finally:
        ping_task.cancel()
        await ws_notification_manager.disconnect(connection)
        logger.info("WS /notifications disconnected: user=%s conn=%s", user.id, connection.id)
