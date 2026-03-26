# RAP-016 Plan

## Objective
Implement password reset and email verification flows with secure token generation, storage, and validation.

## Description
Users need to verify their email after registration and recover their accounts via password reset. Both flows use time-limited, hashed tokens stored in the database. Email delivery uses FastAPI BackgroundTasks with a console backend (actual SMTP deferred to V2 email notification story). Audit logging deferred to V2 audit trail story (RAP-032).

## Acceptance Criteria
- [ ] User model gains `is_verified` boolean field (default false)
- [ ] VerificationToken model stores hashed tokens with type (email_verify/password_reset) and expiry
- [ ] POST /auth/verify-email — accepts token, marks user as verified
- [ ] POST /auth/resend-verification — accepts email, generates new token (no account enumeration)
- [ ] POST /auth/password-reset — accepts email, generates reset token (no account enumeration)
- [ ] POST /auth/password-reset/confirm — accepts token + new password, updates password
- [ ] Login rejects unverified users with clear error message
- [ ] Verification tokens valid for 24 hours, reset tokens for 1 hour
- [ ] Tokens stored as SHA-256 hashes (plaintext never persisted)
- [ ] Tokens are single-use (deleted after successful use)
- [ ] Console email backend logs token URLs for development
- [ ] Unit tests for token generation, hashing, expiry logic
- [ ] Integration tests for all 4 endpoints + login rejection

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified — NO (multiple new endpoints)
- [ ] Solution affects <=3 files — NO (new model, migration, router, schemas, tests)
- [ ] Change impact <=10 lines of actual code — NO
- [ ] Low risk of side effects — NO (modifies login behavior)
- [ ] Solution pattern is well-understood — YES

**Assessment result**: Complex — new model, migration, 4 endpoints, login behavior change, token security

## Approach
1. Add Alembic migration: `is_verified` on users, `verification_tokens` table
2. Create VerificationToken ORM model
3. Create token service (generate, hash, validate, cleanup)
4. Create email backend (console-based, pluggable interface)
5. Add 4 new auth endpoints
6. Modify login to reject unverified users
7. Add schemas for request/response
8. Write unit tests for token service
9. Write integration tests for endpoints

## Dependencies
- Depends on: RAP-007 (JWT Auth — done)
- Blocked by: nothing

## Risks
- Risk: Login behavior change breaks existing tests → Mitigation: update test fixtures to create verified users
- Risk: Token timing attacks → Mitigation: constant-time comparison, uniform response messages
