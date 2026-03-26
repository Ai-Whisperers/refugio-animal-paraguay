# RAP-021 Recap

## Outcome
Delivered secure password reset flow with two-phase token-based recovery. All acceptance criteria met. Email delivery stubbed for V1 (logged instead of sent).

## Acceptance Criteria — Final Status
- [x] `password_reset_tokens` table with migration (005)
- [x] Token generation with 256-bit entropy (`secrets.token_urlsafe`)
- [x] SHA-256 hashed storage — plaintext never persisted
- [x] Constant-time hash comparison (`hmac.compare_digest`)
- [x] 1-hour token expiry
- [x] All user tokens deleted on successful reset
- [x] `POST /auth/password-reset-request` — always returns 200 (anti-enumeration)
- [x] `POST /auth/password-reset/{token}` — validates token, updates password
- [x] Same-password rejection (400)
- [x] Invalid/expired token rejection (404)
- [x] Password minimum length validation (422)
- [x] Full flow tested: request → complete → login with new password
- [x] Unit tests (18) and integration tests (12) passing

## Key Learnings
- Event loop isolation matters for async integration tests — engine singleton must be re-initialized per test when not using shared setup helpers
- Pydantic EmailStr normalizes domain but preserves local part case
- `.test` TLD rejected by email-validator — use `.example.com` for test emails
- Develop branch uses `{"detail": "..."}` error format (RAP-020 not yet merged)

## Validation Evidence
- Tests: 234 passing (96 unit + 138 integration), 0 failing
- Linting: ruff clean
- Type check: mypy clean
- PR: #12 targeting develop
