# RAP-023 Recap

## Outcome
Delivered in-process async event bus infrastructure. All acceptance criteria met.

## Acceptance Criteria — Final Status
- [x] EventBus class with publish/subscribe pattern
- [x] DomainEvent base schema (Pydantic v2, frozen, with UUID id/idempotency_key)
- [x] EventType enum with 10 domain event types (dot-separated namespace)
- [x] 6 concrete event classes with default event_type/aggregate_type
- [x] Idempotency deduplication (same idempotency_key skipped)
- [x] Error isolation (failing handler doesn't block others)
- [x] Non-blocking publish (events queued for async processing)
- [x] Graceful shutdown with queue drain (5s timeout)
- [x] Wired into FastAPI lifespan (auto start/stop)
- [x] get_event_bus dependency for route handlers
- [x] Unit + integration tests

## Key Learnings
- AsyncMock doesn't have `__qualname__` — use `getattr(handler, "__qualname__", repr(handler))` for defensive logging
- pytest-asyncio strict mode requires explicit `@pytest.mark.asyncio` on every async test
- Integration tests that only need the event bus (not DB) should mock init_engine/dispose_engine

## Validation Evidence
- Tests: 170 passing, 0 failing (53 new: 48 unit + 5 integration)
- Ruff: clean
- PR: #14
