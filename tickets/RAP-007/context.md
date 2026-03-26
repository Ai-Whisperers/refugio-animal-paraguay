# RAP-007 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-25

## Current Focus
Ticket closed. All acceptance criteria met.

## Technical State
- Auth module: `src/auth/utils.py`, `src/auth/dependencies.py`, `src/auth/__init__.py`
- Router: `src/api/auth.py` — /auth/token, /auth/users, /auth/me
- Model + migration: `src/db/models/user.py`, `002_create_users_table.py`
- Schemas: `src/schemas/user.py`
- Protected: POST/PATCH/DELETE on /animals, /adopters, /adoption-requests
- Tests: 12 unit (auth utils) + 12 integration (auth endpoints + 401 enforcement)
- bcrypt pinned to <5 to fix passlib compat issue

## Key Decisions Made
- GET endpoints remain public (catalog is public-facing)
- Roles: `staff` and `admin` only (adopter login deferred)
- 30-min token expiry
- bcrypt>=4.0,<5 pin required — bcrypt 5.x removed `__about__` module passlib relies on
- conftest.py uses raw SQL upsert + direct JWT mint (no HTTP login in fixture)
