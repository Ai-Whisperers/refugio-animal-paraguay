---
epic: EPIC-7
title: Admin & Management Dashboards
status: ready
created: 2026-03-25T17:13:26.733586
updated: 2026-03-25T17:13:26.733588
---

# EPIC-7: Admin & Management Dashboards

## Overview

**Goal**: Build the operational management layer that gives shelter staff and administrators a unified view of everything happening at the shelter — animal intake and adoption activity, donation flows, volunteer schedules, and system health — without needing to query the database directly.

**Why it matters**: A small shelter run by a part-time staff team cannot afford to spend significant time constructing manual reports from spreadsheets. The admin dashboard consolidates the most operationally relevant information into fast, authoritative API responses that a frontend interface (built in EPIC-11) will render. Separately, administrators need the ability to manage who has access to which parts of the system — assigning and revoking roles for volunteers, staff, and administrators. Without a user management interface, this requires direct database access, which introduces security risks and excludes non-technical administrators from handling onboarding themselves. Finally, the donor-facing side of the shelter requires credible reporting: European donors who contribute financially expect to see evidence of impact, and the admin reporting endpoints provide the data that backs those reports.

**Target users**: Shelter administrators who need a real-time overview of daily activity and aggregate metrics; shelter staff who need to track task completion and shift coverage; administrators who onboard and manage user accounts and roles; donors (indirectly) who benefit from the accurate reporting that this epic enables.

---

## Scope

### In Scope

- Real-time activity feed: a stream of recent significant events across adoption requests and donations, delivered via a WebSocket endpoint backed by PostgreSQL LISTEN/NOTIFY triggers; includes a REST endpoint for the initial event snapshot (last 20 events) for page load
- Dashboard analytics endpoint: aggregate counts delivered as a single structured response covering the most operationally relevant metrics — animals by status, adoption applications by status, donations received this month versus last month, volunteer shifts with unfilled capacity in the next seven days, and animals on medical hold
- User list and search: a paginated endpoint returning registered users with their role, registration date, and last activity; supports filtering by role and searching by name or email using PostgreSQL case-insensitive pattern matching
- Role management: a single endpoint to update a user's role, with audit logging of who made the change, from what role, to what role, and at what timestamp; enforces that only administrators can modify roles
- Shelter settings management: a table-backed configuration system for shelter-wide settings such as shelter name, contact information, operating hours, and donation configuration values; exposed through authenticated read and write endpoints accessible only to administrators; settings are cached in memory with a short time-to-live to avoid per-request database queries
- Report generation: structured JSON responses aggregating adoption activity, donation totals, and animal population statistics over configurable date ranges; designed to support the donor reporting that the shelter owner uses to communicate with the European funding network
- Data export: CSV export of report data using streaming responses to handle large date ranges without memory issues; UTF-8 with byte-order mark for compatibility with European Excel installations

### Out of Scope

- Frontend rendering of the dashboard (handled by EPIC-11; this epic provides the API layer only)
- Financial accounting or bookkeeping (the shelter owner uses separate financial software; this epic tracks donation totals but does not replace accounting)
- Email campaign management for donors (out of scope for the platform)
- Automated scheduled report delivery via email (a future enhancement)
- Multi-shelter or franchise management views

---

## Stories

- **S01: Admin Dashboard & Analytics** — Implement the aggregate dashboard endpoint that returns a single structured response with key operational metrics drawn from the animals, adoption requests, donations, and volunteer shifts tables. Implement the real-time activity feed using a FastAPI WebSocket endpoint that subscribes to a PostgreSQL NOTIFY channel; a background task listens for INSERT events on the adoption requests and donations tables via asyncpg and broadcasts them to connected WebSocket clients. Implement the REST snapshot endpoint for initial page load. Define the event shape including event type, description, and occurrence timestamp.

- **S02: User & Role Management** — Implement the paginated user list endpoint with name and email search and role filtering. Implement the role update endpoint with input validation against the role enum, an idempotency check that treats no-op updates as successful without writing an audit entry, and an audit log write for genuine changes. Enforce that only users with the admin role can call these endpoints via a FastAPI dependency. Define the response shape for the user list including pagination metadata.

- **S03: Content & Settings Management** — Design the shelter settings table as a structured set of typed configuration rows rather than a free-form key-value store; each setting has a known type and validation constraint. Implement the read endpoint returning all current settings as a typed response. Implement the write endpoint accepting partial updates and validating each submitted value against its type and constraint before persisting. Implement an in-memory cache layer with a configurable time-to-live so that other services reading settings do not hit the database on every request.

- **S04: Reporting & Export** — Implement the report generation endpoints for adoption activity (counts by status per month), donation totals (sum by currency and month), and animal population (counts by status and species over time). Support date range query parameters for all report endpoints. Implement response caching for slow aggregate queries using a short cache with cache invalidation on relevant table writes. Implement the CSV export endpoint that wraps the corresponding report query in a streaming response, selecting the relevant columns and formatting monetary values with their currency symbol for readability.

---

## Dependencies

**Depends on**:
- EPIC-10 (Authentication & User Accounts) — all admin endpoints require authenticated users; the user list and role management endpoints require the admin role; the shelter settings endpoints require the admin role
- EPIC-1 (Animal Catalog & Management) — the dashboard aggregates animal counts by status; activity feed includes adoption application events
- EPIC-2 (Adoption Process & Workflows) — adoption application counts and activity feed events
- EPIC-3 (Donation & Payment Systems) — donation totals by currency and month; donation activity feed events
- EPIC-4 (Medical Records) — count of animals on medical hold visible in the dashboard
- EPIC-5 (Volunteer Management) — volunteer hours analytics and shifts with unfilled capacity

**Blocks**:
- Nothing; EPIC-7 is a consumer of all other data epics

---

## Success Metrics

- The dashboard aggregate endpoint returns a complete response in under 300 milliseconds at the p95 percentile, measured against a database containing six months of operational data
- Real-time activity feed events appear in connected admin clients within two seconds of the triggering database INSERT
- Role updates are reflected in the user's next API request without requiring a re-login, because the role is read from the database on each JWT validation rather than embedded in the token payload
- CSV exports for a 12-month date range complete without timeout and produce a valid, parseable file
- An administrator with no database access can onboard a new staff member from registration to active role assignment in under three minutes using the management interface

---

## Risk Factors

- **WebSocket connection management at scale**: If many admin users are connected simultaneously, the PostgreSQL LISTEN channel may generate significant connection overhead. Mitigation: the WebSocket listener is a single shared background task per server process that fans out to connected clients, rather than one database connection per WebSocket client.
- **Slow aggregate queries on large datasets**: Monthly aggregation queries over adoption and donation tables will slow as data accumulates over months and years. Mitigation: add appropriate indexes on the date columns used in GROUP BY clauses; implement server-side response caching for report endpoints; schedule a performance review after the first six months of production data.
- **Role escalation risk**: The role management endpoint, if improperly secured, could allow a staff user to elevate their own permissions to admin. Mitigation: the endpoint must validate that the authenticated user has the admin role using a FastAPI dependency that runs before the endpoint handler; this must be covered by integration tests verifying that a staff-role JWT is rejected with a 403 response.
- **Settings cache invalidation**: If multiple server instances are running and one instance updates a shelter setting, the other instances' caches will serve stale data until their time-to-live expires. Mitigation: keep the cache time-to-live short (under five minutes) and document this behavior; for settings that are truly critical (such as donation configuration), consider bypassing the cache on write operations.

---

## Effort & Priority

**Priority**: Medium. The admin dashboard delivers significant operational value to the shelter owner and staff but does not block adopters or donors from using the platform's core workflows. It should be delivered once EPIC-1, EPIC-2, EPIC-3, and EPIC-5 are stable enough to provide meaningful data.

**Estimated effort**: Two sprints. The dashboard analytics and user management (S01, S02) are the highest-priority deliverables and form the first sprint. Settings management and reporting with export (S03, S04) follow in the second sprint.
