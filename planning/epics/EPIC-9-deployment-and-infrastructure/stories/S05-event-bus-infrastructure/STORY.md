---
story: S05
epic: EPIC-9
title: Event Bus Infrastructure
status: ready
created: 2026-03-26T00:00:00.000000
effort: 8
---

# S05: Event Bus Infrastructure

## User Story

As a **developer**, I want to **implement an event bus for domain events so that adoption status changes, donations, medical alerts, and volunteer events decouple from their handlers** so that **the system is scalable, testable, and can support multiple subscribers without tight coupling**.

## Acceptance Criteria

**Given** an adoption status changes
**When** the status update is persisted
**Then** an AdoptionStatusChanged event is published to the event bus

**Given** an event is published to the bus
**When** the event bus receives it
**Then** all registered subscribers are notified asynchronously

**Given** the notification system subscribes to adoption events
**When** an adoption status changes
**Then** the notification handler receives the event and triggers email notifications

**Given** the dashboard system subscribes to multiple domain events
**When** events are published
**Then** the dashboard handler receives and processes them for real-time updates

**Given** an event is published with all required metadata
**When** I inspect the event
**Then** I can see event_type, payload, timestamp, actor_id, and idempotency_key

**Given** the system needs to scale from in-process to distributed messaging
**When** I review the event bus design
**Then** the interface supports upgrading from asyncio to Redis pub/sub without handler changes

## Tasks

- T01: Design event bus interface with publish(event) and subscribe(event_type, handler) methods
- T02: Implement in-process async event dispatcher using Python asyncio with queue management
- T03: Define standard event schema (event_type: enum, payload: dict, timestamp, actor_id, idempotency_key)
- T04: Create event registration for adoption, donation, medical, and volunteer domains with concrete event classes
- T05: Write unit tests with mock subscribers and integration tests verifying multi-subscriber delivery

## Definition of Done

- [ ] Event bus interface defined with publish() and subscribe() methods
- [ ] In-process dispatcher implemented using asyncio.Queue with error handling
- [ ] Standard event schema includes event_type (enum), payload, timestamp, actor_id, idempotency_key
- [ ] Event classes created: AdoptionStatusChanged, DonationReceived, MedicalAlert, VolunteerShiftCreated, etc.
- [ ] Subscribers (notification, dashboard, audit trail) register with event bus at startup
- [ ] Event publishing is async (non-blocking) with retry logic for failed handlers
- [ ] Unit tests cover publish/subscribe mechanics, event schema validation, and error scenarios (80%+ coverage)
- [ ] Integration tests verify multiple subscribers receiving same event and event ordering
- [ ] Handler error isolation: one failing subscriber doesn't block others
- [ ] Idempotency key prevents duplicate processing of retried events

## Technical Notes

- Event bus interface:
  ```python
  class EventBus:
      async def publish(event: DomainEvent) -> None
      def subscribe(event_type: str, handler: Callable) -> None
      async def unsubscribe(event_type: str, handler: Callable) -> None
  ```
- DomainEvent schema: id (UUID), event_type (enum), payload (dict), timestamp (ISO 8601), actor_id (UUID), idempotency_key (UUID), aggregate_id, aggregate_type
- Event dispatcher: Single asyncio.Queue per event_type, dedicated task per event type consuming and dispatching to subscribers
- Event types enum: "adoption.status_changed", "donation.received", "medical.alert_created", "volunteer.shift_created", "volunteer.shift_completed", "animal.intake_completed", etc.
- Error handling: If handler raises exception, log error, publish ErrorEvent, continue to next subscriber
- Ordering guarantee: Events published in order are processed in order (per event type)
- Database indexes: For event log table (future): event_type, actor_id, aggregate_id, timestamp
- V2-V4 uses in-process asyncio; V5 roadmap: upgrade to Redis pub/sub for distributed deployment

## Dependencies

- Depends on: None (foundational infrastructure)
- Blocks: EPIC-6 (Notification system), EPIC-7 (Dashboard real-time updates), EPIC-13 (Audit trail event logging)

## Story Points: 8
