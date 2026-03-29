# RAP-224 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-29 00:30

## Technical State
- src/services/ws_notification_manager.py: connection manager, broadcast_to_user, broadcast_to_all
- src/api/notifications_ws.py: /ws/notifications endpoint, JWT auth, ping loop
- src/app.py: includes notifications_ws_router
- frontend/src/hooks/useWebSocketNotifications.ts: React hook with exponential back-off reconnect
- tests/unit/test_ws_notification_manager.py: 7 unit tests, all passing

## Key Decisions Made
- JWT via query param (same as SSE admin endpoint) — EventSource/WS can't set headers
- Ping every 25s to keep alive through Traefik
- Exponential back-off reconnect (1s → 30s max) in frontend
- WSNotificationManager is a singleton shared across the app lifecycle
