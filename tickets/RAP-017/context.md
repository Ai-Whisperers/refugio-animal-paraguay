# RAP-017 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26 11:00

## Current Focus
Creating ticket structure and starting implementation.

## Technical State
- No existing event system in the codebase
- FastAPI app with async SQLAlchemy — event bus fits naturally with asyncio
- Designed as in-process first, upgradable to Redis pub/sub later

## Next Steps
1. Create feature branch
2. Implement event bus module
3. Write tests

## Blockers
- None

## Key Decisions Made
- In-process asyncio dispatcher (not Redis/Celery — can upgrade later)
- Dataclass-based events (not Pydantic — lightweight, no validation overhead for internal events)
- Fire-and-forget semantics with error isolation per handler
