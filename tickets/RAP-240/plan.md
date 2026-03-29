# RAP-240 Plan

## Objective
Add Content Security Policy (CSP) and HTTP security headers middleware to harden the FastAPI backend against XSS, clickjacking, and other injection attacks.

## Description
The API currently has no CSP or security headers beyond CORS. This middleware adds production-grade HTTP security headers including Content-Security-Policy, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and Permissions-Policy. Headers are environment-aware: stricter in production, relaxed in development to allow hot-reload and inline scripts.

## Acceptance Criteria
- [x] CSP header added to all API responses
- [x] HSTS header added for production (min 1 year)
- [x] X-Frame-Options: DENY set
- [x] X-Content-Type-Options: nosniff set
- [x] Referrer-Policy set to strict-origin-when-cross-origin
- [x] Permissions-Policy set to deny sensitive permissions
- [x] Middleware registered in app.py
- [x] Unit tests cover header presence per environment
- [x] Integration test for happy path

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files
- [x] Change impact ≤10 lines of actual code (per file)
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Simple Fix — adds a new middleware, wires it into app.py, adds tests. No DB or API changes.

## Approach
1. Create `src/middleware/security_headers.py` — SecurityHeadersMiddleware
2. Register in `src/app.py`
3. Write unit + integration tests in `tests/unit/test_security_headers_middleware.py`

## Dependencies
- None

## Risks
- Risk: CSP may break frontend in development → Mitigation: Relax `unsafe-inline` in dev mode
