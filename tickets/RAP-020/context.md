# RAP-020 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26

## Current Focus
Starting implementation of CORS, rate limiting, and error standardization.

## Technical State
- FastAPI app in src/app.py with lifespan and routers
- Config in src/config.py (pydantic-settings)
- No existing middleware directory
- Need to add slowapi dependency

## Next Steps
1. Install slowapi, add to pyproject.toml
2. Add config settings
3. Implement error schema and handlers
4. Wire up CORS and rate limiting

## Blockers
None

## Key Decisions Made
- Use slowapi for rate limiting (built on top of limits library, FastAPI-native)
- In-memory rate limit storage (sufficient for single-instance MVP)
- CORS origins from comma-separated env var
