# RAP-023 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26

## Current Focus
Starting implementation — creating event bus core and domain events.

## Technical State
- No event system exists yet
- asyncio-based in-process dispatcher (Redis upgrade path for V5)
- Will live in `src/events/` package

## Next Steps
1. Create src/events/ package structure
2. Define DomainEvent base class and EventType enum
3. Implement EventBus dispatcher

## Blockers
None

## Key Decisions Made
- In-process asyncio for V2-V4, Redis pub/sub deferred to V5
- Event bus registered at app startup, cleaned up at shutdown
