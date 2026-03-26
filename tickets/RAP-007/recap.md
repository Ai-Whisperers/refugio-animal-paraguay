# RAP-007 Recap

## Outcome
Delivered full JWT authentication for staff/admin roles. All planned components implemented and committed.

## Acceptance Criteria — Final Status
- [x] POST /auth/token — login with email+password, returns JWT bearer token
- [x] GET /auth/me — returns current user profile from token
- [x] POST /auth/users — admin-only user creation
- [x] POST /animals, PATCH /animals/:id, DELETE /animals/:id — require valid JWT (401 without)
- [x] POST /adopters, PATCH /adopters/:id, DELETE /adopters/:id — require valid JWT
- [x] POST /adoption-requests, PATCH /adoption-requests/:id/status — require valid JWT
- [x] GET endpoints remain public
- [x] Passwords stored as bcrypt hashes (cost 12)
- [x] 12 unit tests for password hashing and JWT utilities
- [x] 12 integration tests for auth endpoints and 401 enforcement
- [x] All 163+ tests pass

## Key Learnings
- bcrypt 5.0.0 broke passlib 1.7.4 — removed `__about__` module passlib uses to detect backend. Pin `bcrypt>=4.0,<5` in pyproject.toml.
- conftest.py client fixture should upsert the staff user via raw SQL + mint JWT directly to avoid circular dependency on the auth endpoint under test.
- 4 existing test files each had their own `client` fixture shadowing conftest — removed them all.

## Validation Evidence
- Tests: 163 passing, 0 failing
- Pyright: 0 errors, 0 warnings
- Commit: a42b02a
