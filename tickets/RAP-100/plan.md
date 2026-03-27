# RAP-100 Plan

## Objective
Create a staff login page at /admin/login that authenticates against the existing JWT backend.

## Description
Staff members need a dedicated admin login page to access shelter management tools. The page authenticates via the existing POST /auth/token endpoint and stores the JWT for subsequent admin API calls.

## Acceptance Criteria
- [x] Login page at /admin/login with email/password form
- [x] Valid credentials return JWT token and redirect to /admin/dashboard
- [x] Invalid credentials show error message, remain on login page
- [x] Expired token redirects to login with session expired message
- [x] Admin layout without public Navbar/Footer

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects <= 3 files
- [ ] Change impact <= 10 lines of actual code (more, but straightforward)
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Simple — standard Next.js page with fetch to existing API

## Approach
1. Create admin layout (no public nav/footer)
2. Create login page with form, error handling, loading states
3. Create dashboard placeholder with auth guard
4. Create /admin redirect based on auth state

## Dependencies
- Depends on: existing /auth/token endpoint (RAP-007, done)

## Risks
- Risk: sessionStorage not available in SSR → Mitigation: in-memory fallback already exists in auth.ts
