# RAP-224 Plan

## Objective
Add real-time WebSocket notification delivery to replace polling for in-app notifications.

## Description
Currently the NotificationCenter polls every 30s for new notifications. This story adds a WebSocket endpoint (/ws/notifications) that pushes notifications in real-time when events occur. Staff authenticate via JWT query param. The frontend hook useWebSocketNotifications connects and reconnects with exponential back-off.

## Acceptance Criteria
- [ ] WSNotificationManager manages per-user WebSocket connections
- [ ] /ws/notifications endpoint authenticates via JWT query param
- [ ] Server sends {"event": "notification", "data": {...}} on new notifications
- [ ] Server sends periodic {"event": "ping"} keep-alive messages
- [ ] Client hook reconnects with exponential back-off on disconnect
- [ ] Unit tests for WSNotificationManager pass
- [ ] ruff clean on all new Python files

## Complexity Assessment
**Track**: Complex — backend WebSocket infrastructure + frontend hook. Fullstack.

## Approach
1. WSNotificationManager service: manages connections, broadcast
2. notifications_ws.py: FastAPI WebSocket endpoint with JWT auth
3. Register in app.py
4. useWebSocketNotifications hook: connect, parse, reconnect

## Risks
- Risk: WebSocket not supported by all load balancers → Mitigation: standard WS protocol, Traefik v3 supports it
