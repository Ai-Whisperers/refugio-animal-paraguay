# RAP-023 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-26

## Current Focus
Completed — event bus infrastructure delivered.

## Technical State
- `src/events/` package: types.py, bus.py, domain_events.py, dependencies.py, __init__.py
- EventBus wired into FastAPI lifespan (auto start/stop)
- `get_event_bus` FastAPI dependency for route handlers
- 53 tests (48 unit + 5 integration), all 170 project tests passing

## Blockers
None

## Key Decisions Made
- In-process asyncio for V2-V4, Redis pub/sub deferred to V5
- Event bus registered at app startup via lifespan, cleaned up at shutdown
- One asyncio.Queue per event type for ordering guarantees
- Idempotency via UUID idempotency_key (checked at publish + consume)
- Error isolation: handler exceptions logged, not propagated
- StrEnum for EventType (Python 3.12+)
