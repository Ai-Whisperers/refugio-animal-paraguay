# RAP-013 Plan

## Objective
Add CORS middleware, rate limiting, and standardized error responses so the API is secure, predictable, and ready for frontend integration.

## Description
The API currently returns raw FastAPI/Pydantic error responses with no CORS headers and no rate limiting. Frontend development (EPIC-11) is blocked until CORS is configured. Public endpoints are vulnerable to abuse without rate limiting. Error responses are inconsistent across endpoints, making client-side error handling fragile.

## Acceptance Criteria
- [ ] CORS middleware configured with ALLOWED_ORIGINS env var (comma-separated)
- [ ] Rate limiting active: 5/min on auth endpoints, 60/min on general endpoints
- [ ] Rate limit headers on all responses (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- [ ] Standard ErrorResponse schema: { error_code, message, details, request_id }
- [ ] Exception handlers for: ValidationError, HTTPException, RateLimitExceeded, unhandled
- [ ] No internal details leaked in 500 responses
- [ ] RATE_LIMIT_ENABLED toggle in settings
- [ ] Unit tests for error formatting
- [ ] Integration tests for rate limiting (429 trigger) and CORS headers
- [ ] All existing tests still pass

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified — N/A, multi-concern
- [x] Solution affects ≤3 files — ~8 files affected
- [ ] Change impact ≤10 lines of actual code — ~300+ lines
- [ ] Low risk of side effects — middleware affects all endpoints
- [ ] Solution pattern is well-understood

**Assessment result**: Complex — touches config, middleware, schemas, app factory, and all response paths. Phased approach.

## Approach

### Phase 1: Error Standardization
1. Create `src/schemas/error.py` — ErrorResponse, ValidationErrorDetail
2. Create `src/middleware/error_handler.py` — exception handlers
3. Register handlers in `src/app.py`

### Phase 2: CORS
4. Add ALLOWED_ORIGINS to `src/config.py`
5. Add CORSMiddleware in `src/app.py`

### Phase 3: Rate Limiting
6. Add slowapi dependency
7. Create `src/middleware/rate_limit.py` — limiter setup
8. Add RATE_LIMIT_ENABLED to `src/config.py`
9. Apply rate limits to auth router and global default

### Phase 4: Tests
10. Unit tests for error formatting (test_error_schema.py)
11. Integration tests for CORS headers and rate limiting (test_cors_rate_limit.py)

## Dependencies
- Depends on: Docker setup (RAP-010) — DONE
- Blocks: Next.js scaffold (#4), Animal Browsing Page (#5), all frontend stories

## Risks
- Risk: slowapi not compatible with async FastAPI → Mitigation: slowapi supports async; fallback to custom middleware
- Risk: Rate limiting breaks existing integration tests → Mitigation: RATE_LIMIT_ENABLED=false in test config
