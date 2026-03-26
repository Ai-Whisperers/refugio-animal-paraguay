---
story: S01
epic: EPIC-0
title: CORS, Rate Limiting, and Error Standardization
status: ready
created: 2026-03-26T00:00:00.000000
effort: 5
---

# S01: CORS, Rate Limiting, and Error Standardization

## User Story

As an **API consumer**, I want **consistent error responses, CORS headers for frontend integration, and rate limiting to prevent abuse** so that **the API is secure, predictable, and ready for frontend development**.

## Acceptance Criteria

**Given** a frontend running on a configured origin
**When** it makes a request to the API
**Then** CORS headers allow the request and credentials are supported

**Given** a client exceeding the rate limit on auth endpoints
**When** it sends more than 5 requests per minute to /auth/*
**Then** it receives a 429 response with Retry-After header and standard error format

**Given** a client exceeding the general API rate limit
**When** it sends more than 60 requests per minute
**Then** it receives a 429 with rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)

**Given** any API error occurs
**When** the response is returned
**Then** it follows the standard format: { error_code, message, details, request_id }

**Given** a validation error
**When** a request has invalid fields
**Then** the 422 response includes field-level error details

## Definition of Done

- [ ] CORS middleware configured with ALLOWED_ORIGINS env var
- [ ] Rate limiting active: 5/min on auth, 60/min on general endpoints
- [ ] Rate limit headers present on all responses
- [ ] Standard ErrorResponse schema used across all error responses
- [ ] Exception handlers registered for: ValidationError, HTTPException, RateLimitExceeded, unhandled
- [ ] No internal details leaked in 500 responses
- [ ] RATE_LIMIT_ENABLED toggle in settings
- [ ] Unit tests for error formatting
- [ ] Integration tests for rate limiting (429 trigger) and CORS headers
- [ ] All existing tests still pass

## Technical Notes

- CORS: FastAPI CORSMiddleware, origins from ALLOWED_ORIGINS env (comma-separated)
- Rate limiting: slowapi library with in-memory storage
- Error schema: src/schemas/error.py — ErrorResponse(error_code, message, details, request_id)
- Exception handlers: src/middleware/error_handler.py
- Config additions to src/config.py: ALLOWED_ORIGINS, RATE_LIMIT_ENABLED

## Dependencies

- Depends on: EPIC-9 S01 (Docker setup — delivered as RAP-010)
- Blocks: Frontend stories (EPIC-11) need CORS to work

## Story Points: 5
