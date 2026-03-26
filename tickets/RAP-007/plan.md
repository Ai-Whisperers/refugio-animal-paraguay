# RAP-007 Plan

## Objective
Add JWT authentication with password-based login, a users table, and role-based access control protecting all mutation endpoints.

## Description
The API is currently fully open — anyone can create, modify, or delete any record. Before the platform can be deployed, mutations must be protected. Staff (shelter employees) need credentials to manage animals and adoption requests. Adopters will eventually log in too, but the initial scope is staff auth covering the admin-side operations.

## Acceptance Criteria
- [ ] `users` table: id, email (unique), hashed_password, role (`staff` | `admin`), is_active, created_at, updated_at
- [ ] Alembic migration 002 creates the users table
- [ ] `POST /auth/token` — email + password → JWT access token (30 min expiry)
- [ ] `POST /auth/users` — admin-only: create a new staff/admin user
- [ ] `GET /auth/me` — returns current user from token
- [ ] `require_staff` dependency: verifies valid JWT with role staff or admin
- [ ] `require_admin` dependency: verifies valid JWT with role admin only
- [ ] Animals: POST/PATCH/DELETE protected with `require_staff`
- [ ] Adopters: POST/PATCH/DELETE protected with `require_staff`
- [ ] Adoption requests: POST/PATCH protected with `require_staff`
- [ ] GET endpoints remain public (catalog is public-facing)
- [ ] Unit tests for auth utilities (password hashing, token encode/decode)
- [ ] Integration tests for all auth endpoints + 401 enforcement on protected routes
- [ ] Zero Pyright errors

## Complexity Assessment
**Track**: Complex — new DB table, migration, new router, dependency injection wired across 3 existing routers, security-sensitive code

## Approach
Phase 1: DB model + migration + password/JWT utilities
Phase 2: Auth router (login, create user, me)
Phase 3: Wire `require_staff`/`require_admin` into existing routers
Phase 4: Tests

## Dependencies
- Depends on: RAP-004, RAP-005, RAP-006 (all complete)

## Risks
- Risk: Weak JWT secret in dev bleeds to prod → Mitigation: validate SECRET_KEY length in Settings (min 32 chars)
- Risk: bcrypt cost factor too low → Mitigation: use 12 rounds (standard)
