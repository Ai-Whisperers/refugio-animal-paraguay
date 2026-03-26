# RAP-020 Plan

## Objective
Add CORS, rate limiting, and standardized error responses to harden the API for frontend integration.

## Description
The API needs CORS for frontend development, rate limiting to prevent abuse (especially on auth endpoints), and a consistent error response format across all endpoints. This is a cross-cutting concern that touches middleware and exception handling.

## Acceptance Criteria
- [ ] CORS middleware with ALLOWED_ORIGINS env var (comma-separated)
- [ ] Rate limiting: 5/min on /auth/*, 60/min on general endpoints
- [ ] Rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
- [ ] 429 responses with Retry-After header
- [ ] Standard ErrorResponse: { error_code, message, details, request_id }
- [ ] Exception handlers for ValidationError, HTTPException, RateLimitExceeded, unhandled
- [ ] No internal details leaked in 500 responses
- [ ] RATE_LIMIT_ENABLED config toggle
- [ ] Unit tests for error formatting
- [ ] Integration tests for CORS headers and rate limiting

## Complexity Assessment
**Track**: Complex Implementation

- Cross-cutting middleware changes
- New dependency (slowapi)
- Custom exception handlers
- Config additions

**Assessment result**: Complex — multiple middleware layers, affects all endpoints

## Approach
1. Add slowapi dependency to pyproject.toml, pip install
2. Add ALLOWED_ORIGINS and RATE_LIMIT_ENABLED to config.py
3. Create src/schemas/error.py — ErrorResponse schema
4. Create src/middleware/error_handler.py — exception handlers
5. Create src/middleware/rate_limiter.py — rate limiting setup
6. Wire CORS + rate limiting + error handlers into app.py
7. Write tests
8. Run quality gates

## Dependencies
- No blockers
- Blocks: Frontend stories need CORS

## Risks
- Risk: slowapi may not work well with async → Mitigation: use SlowAPI with default in-memory store, well-supported
