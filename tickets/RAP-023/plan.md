# RAP-023 Plan

## Objective
Implement an in-process async event bus for domain events, enabling decoupled event-driven architecture.

## Description
The system needs an event bus to decouple domain operations from their side effects. When an adoption status changes, a donation is received, or a medical alert is created, the event bus publishes domain events that any number of subscribers can handle asynchronously. This is foundational infrastructure that blocks notifications, dashboard updates, and audit logging.

## Acceptance Criteria
- [ ] EventBus interface with publish(), subscribe(), unsubscribe() methods
- [ ] In-process async dispatcher using asyncio
- [ ] Standard DomainEvent schema: id, event_type, payload, timestamp, actor_id, idempotency_key, aggregate_id, aggregate_type
- [ ] Concrete event classes: AdoptionStatusChanged, DonationReceived, MedicalAlert, VolunteerShiftCreated, AnimalIntakeCompleted
- [ ] Multiple subscribers receive the same event
- [ ] Handler error isolation: one failing subscriber doesn't block others
- [ ] Idempotency key prevents duplicate processing
- [ ] Event publishing is non-blocking
- [ ] Unit tests for publish/subscribe mechanics and error scenarios
- [ ] Integration tests for multi-subscriber delivery

## Complexity Assessment
**Track**: Complex Implementation

- New architectural component (event bus)
- Multiple new files: event bus core, domain events, event types enum
- Async queue management with error handling
- Needs careful design for future Redis upgrade path

**Assessment result**: Complex — new architectural pattern, 6+ files, async concurrency

## Approach
1. Create `src/events/` package
2. Define DomainEvent base schema and EventType enum
3. Implement EventBus with asyncio-based dispatch
4. Create concrete domain event classes
5. Write comprehensive unit tests
6. Write integration tests for multi-subscriber scenarios
7. Wire event bus into app lifecycle (startup/shutdown)

## Dependencies
- Depends on: None (foundational)
- Blocks: Notifications (EPIC-6), Dashboard (EPIC-7), Audit Trail (EPIC-13)

## Risks
- Risk: Async error handling complexity → Mitigation: Robust error isolation with logging
- Risk: Memory leaks from unprocessed events → Mitigation: Queue size limits and monitoring
