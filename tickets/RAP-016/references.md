# RAP-016 References

## Key Files
- `src/db/models/user.py` — User model (adding is_verified)
- `src/auth/utils.py` — Password hashing, JWT utilities
- `src/auth/dependencies.py` — Auth dependencies (require_staff etc.)
- `src/api/auth.py` — Auth router (login, create user, me)
- `src/schemas/user.py` — User schemas
- `src/config.py` — Settings
- `tests/integration/conftest.py` — Test fixtures (need update for is_verified)

## New Files
- `src/db/models/verification_token.py` — Token model
- `src/auth/token_service.py` — Token generation, validation, cleanup
- `src/auth/email_backend.py` — Console email backend
- `src/schemas/password_reset.py` — Request/response schemas
- `src/db/alembic/versions/006_add_email_verification.py` — Migration
- `tests/unit/test_token_service.py` — Token service unit tests
- `tests/integration/test_password_reset.py` — Integration tests

## Story
- `planning/epics/EPIC-10-authentication-and-user-accounts/stories/S02-password-reset-and-email-verification/STORY.md`
