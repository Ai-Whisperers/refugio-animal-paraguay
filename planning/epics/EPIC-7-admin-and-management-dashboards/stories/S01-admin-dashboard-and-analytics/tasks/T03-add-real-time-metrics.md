---
task: T03
story: S01
epic: EPIC-7
title: Add real-time metrics
---

# T03 — Add Real-Time Activity Metrics Feed

## Objective

Implement a live activity feed on the admin dashboard that displays the most recent adoption requests and donation events as they occur, without requiring the admin to manually refresh the page.

## Background and Rationale

The admin dashboard provides shelter staff with an overview of daily operations. A static view that requires manual refresh is inadequate for a busy shelter — staff need to see adoption applications and incoming donations as they happen. The real-time feed solves this by streaming INSERT events from the database directly to the browser session.

The implementation uses two complementary mechanisms: a REST endpoint for the initial data load when the page is first opened, and a WebSocket connection that pushes subsequent events as they arrive. This keeps the initial page load fast while ensuring the feed stays current without polling.

## Architecture Overview

The real-time capability is built on PostgreSQL's LISTEN/NOTIFY feature, which allows the database to broadcast notifications to connected listeners when rows are inserted into specific tables. FastAPI maintains a persistent async connection to the database via asyncpg and forwards those notifications over a WebSocket connection to each connected admin browser session.

## PostgreSQL Trigger and Notification Setup

A PostgreSQL trigger function is created that fires on every INSERT into the `adoption_requests` table and separately on every INSERT into the `donations` table. When triggered, the function calls `pg_notify` with a channel name of `admin_activity` and a JSON payload containing the event type, a human-readable description, and the UTC timestamp of the event.

For an adoption request event, the payload describes which adopter submitted a request and for which animal. For a donation event, the payload describes the amount, currency, and a reference to the donor. The payload is kept minimal — it carries enough information to display one line in the activity feed without requiring a follow-up query.

Both triggers are created via an Alembic migration, so the database setup is version-controlled and reproducible across all environments. The migration defines the trigger function and attaches the triggers to both tables. Rolling back the migration drops the triggers and the function cleanly.

## FastAPI WebSocket Endpoint

The backend exposes a WebSocket endpoint at the path `/ws/admin/activity`. When a client connects, the endpoint authenticates the connection by validating a JWT token passed as a query parameter, because WebSocket handshakes in browsers do not support the Authorization header used by standard REST requests. Only users with the `admin` or `staff` role are permitted to connect.

After successful authentication, the endpoint opens an asyncpg connection and issues a PostgreSQL LISTEN command on the `admin_activity` channel. The endpoint then enters an async loop waiting for notifications. When a notification arrives from the database, the endpoint reads its payload and sends it to the WebSocket client as a JSON message.

The endpoint uses FastAPI's async infrastructure, so a single worker process can hold many concurrent WebSocket connections open without blocking. Each connected admin session has its own asyncpg listener connection.

## Initial Snapshot Endpoint

When a browser first loads the admin dashboard, it needs to display recent activity before any new events have arrived via WebSocket. A separate REST endpoint handles this initial load at `GET /admin/activity/recent`.

This endpoint queries both the `adoption_requests` and `donations` tables, combines the results, sorts by `created_at` descending, and returns the twenty most recent events. The query joins each source table with its relevant related tables to assemble the same event shape used by the live WebSocket notifications. The response is a JSON array of event objects.

This endpoint also requires admin or staff authentication via the standard JWT Bearer dependency injection pattern used throughout the application.

## Event Shape

Every event — whether delivered via the initial REST snapshot or the ongoing WebSocket stream — has a consistent three-field shape. The `type` field contains either the string `adoption` or `donation`. The `description` field contains a single human-readable sentence suitable for display in the feed. The `occurred_at` field contains the event timestamp in ISO 8601 UTC format.

This consistency means the frontend needs only one rendering component for both event types and can handle REST and WebSocket payloads with the same logic.

The feed is capped at twenty visible items. When a new event arrives via WebSocket, the frontend prepends it and trims the oldest item if the list exceeds twenty entries.

## Frontend Integration

The frontend (stack TBD) handles two phases at page load. First, it calls the REST snapshot endpoint to populate the initial list and renders those items immediately. Second, it opens the WebSocket connection to begin receiving live events. From that point forward, arriving WebSocket messages are prepended to the displayed list.

The frontend is responsible for reconnection handling. If the WebSocket connection drops due to a network interruption or server restart, the client attempts to reconnect using exponential backoff starting at one second and increasing up to a maximum of thirty seconds between retries. On successful reconnect, the frontend re-fetches the REST snapshot to fill any events missed during the disconnection window.

## Connection Lifecycle and Error Handling

Each WebSocket connection corresponds to one asyncpg listener. When the WebSocket disconnects — whether the client closes the tab, the network drops, or the server sends a close frame — the endpoint cancels the listener loop and closes the asyncpg connection, releasing it back to the pool.

If the asyncpg LISTEN connection is lost while the WebSocket is still open, the endpoint sends a structured error message to the client instructing it to reconnect, then closes the WebSocket cleanly so the frontend's reconnect logic activates.

## Testing Strategy

Unit tests cover the notify payload builder functions, verifying that given a database row from `adoption_requests` or `donations`, the correct JSON shape is produced with the right field names and values.

Integration tests run against a real PostgreSQL test instance. One test inserts a row into `adoption_requests` and then checks that a NOTIFY was received on the `admin_activity` channel with the expected payload. A second integration test does the same for `donations`. These confirm that the Alembic migration wired the triggers correctly.

A third integration test exercises the full WebSocket path: it connects as an authenticated admin user, inserts a row into `adoption_requests` via a direct database operation, and asserts that the WebSocket client receives the corresponding event within a bounded timeout. This tests the complete path from database INSERT through the asyncpg listener to the WebSocket client.

## Files Involved

The Alembic migration containing the trigger function and LISTEN/NOTIFY setup lives in the `migrations/` directory. The asyncpg listener logic and WebSocket connection handling live in a module under `src/realtime/`. The WebSocket endpoint route is registered in the admin router. The REST snapshot endpoint is co-located with the other dashboard routes in the admin router. The Pydantic schema for the activity event shape is defined in the schemas module and shared between both endpoints.
