# RAP-017 Plan

## Objective
Implement an in-process async event bus for domain events, enabling decoupled communication between services.

## Description
The system needs an event-driven architecture to decouple domain actions (adoption changes, donations, medical alerts) from their side effects (notifications, audit logging, dashboard updates). This story implements the event bus infrastructure with an in-process asyncio dispatcher, standard event schema, and concrete event classes.

## Acceptance Criteria
- [ ] Event bus interface with publish() and subscribe() methods
- [ ] In-process async dispatcher using asyncio with error handling
- [ ] Standard event schema: event_type, payload, timestamp, actor_id, idempotency_key
- [ ] Concrete event classes: AdoptionStatusChanged, DonationReceived, MedicalAlert, VolunteerShiftCreated
- [ ] Handler error isolation: one failing subscriber doesn't block others
- [ ] Retry logic for failed handlers (configurable)
- [ ] Unit tests for publish/subscribe, event schema, error isolation (80%+)
- [ ] Integration tests for multi-subscriber delivery

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — new module, multiple classes, async patterns, error handling

## Approach
1. Define event base schema (dataclass with standard fields)
2. Define concrete event classes per domain
3. Implement EventBus class with asyncio-based dispatcher
4. Add error isolation and retry for handlers
5. Register bus in app lifespan
6. Write comprehensive tests

## Dependencies
- Depends on: nothing (standalone infrastructure)
- Blocked by: nothing

## Risks
- Risk: Asyncio event handling complexity → Mitigation: keep dispatcher simple, use asyncio.create_task
- Risk: Memory leaks from uncollected handlers → Mitigation: weak references or explicit unsubscribe
