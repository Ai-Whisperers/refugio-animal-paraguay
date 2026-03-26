# RAP-022 Plan

## Objective
Add CORS middleware, rate limiting, and standardized error responses to the API.

## Description
The API needs CORS headers for frontend integration, rate limiting to prevent abuse (especially on auth endpoints), and a consistent error response format across all endpoints. This is a cross-cutting concern that unblocks frontend development (EPIC-11).

## Acceptance Criteria
- [ ] CORS middleware configured with ALLOWED_ORIGINS env var (comma-separated)
- [ ] Rate limiting active: 5/min on auth endpoints, 60/min on general endpoints
- [ ] Rate limit headers present on responses (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- [ ] 429 responses include Retry-After header and standard error format
- [ ] Standard ErrorResponse schema: { error_code, message, details, request_id }
- [ ] Exception handlers for: ValidationError, HTTPException, RateLimitExceeded, unhandled
- [ ] No internal details leaked in 500 responses
- [ ] RATE_LIMIT_ENABLED toggle in settings
- [ ] Unit tests for error formatting
- [ ] Integration tests for rate limiting and CORS headers
- [ ] All existing tests still pass

## Complexity Assessment
**Track**: Complex Implementation

- Multiple middleware layers (CORS, rate limiting, error handling)
- Touches app factory, config, and creates new middleware/schema modules
- Must not break existing 234 tests

**Assessment result**: Complex — multiple files, middleware integration, needs careful test isolation

## Approach
1. Add slowapi to project dependencies
2. Extend Settings with ALLOWED_ORIGINS, RATE_LIMIT_ENABLED, rate limit values
3. Create src/schemas/error.py with ErrorResponse schema
4. Create src/middleware/error_handler.py with exception handlers
5. Add CORS middleware to app factory
6. Add rate limiting via slowapi to app + auth-specific limits
7. Write unit tests for error formatting
8. Write integration tests for rate limiting (429 trigger) and CORS headers

## Dependencies
- Depends on: RAP-010 (Docker setup — delivered)
- Blocks: EPIC-11 frontend stories (need CORS)

## Risks
- Risk: Rate limiting could affect existing integration tests → Mitigation: RATE_LIMIT_ENABLED=false in test env
- Risk: Error handler changes could break existing response assertions → Mitigation: Keep FastAPI default detail format as fallback
