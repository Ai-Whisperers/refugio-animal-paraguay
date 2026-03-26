# RAP-021 Plan

## Objective
Implement a secure password reset flow allowing users to reset their forgotten passwords via email-based tokens.

## Description
This is the V1 partial implementation of EPIC-10 S02 (Password Reset and Email Verification). For V1, we implement the password reset flow only — email verification is deferred to V5. The flow includes: request a reset (generates a secure token, "sends" email via background task), and complete a reset (validate token, update password). Tokens are SHA-256 hashed in the DB, expire after 1 hour, and are single-use.

## Acceptance Criteria
- [ ] POST /auth/password-reset-request accepts email, always returns 200 (no account enumeration)
- [ ] Reset tokens generated with >= 128 bits entropy (secrets.token_urlsafe)
- [ ] Tokens stored as SHA-256 hashes in password_reset_tokens table
- [ ] Tokens expire after 1 hour
- [ ] POST /auth/password-reset/{token} accepts new password, validates strength, updates user
- [ ] Password strength: min 8 chars (matching existing UserCreate schema)
- [ ] Used tokens are deleted; all user tokens deleted on successful reset
- [ ] Invalid/expired tokens return generic 404 (no information leak)
- [ ] Alembic migration 005 creates password_reset_tokens table
- [ ] Unit tests for token generation, password validation, schemas
- [ ] Integration tests for full reset flow
- [ ] All quality gates pass (ruff, mypy, black, pytest)

## Complexity Assessment
**Track**: Complex Implementation

- Multiple files: model, migration, schemas, service, endpoints, tests
- Security-sensitive: token hashing, no info leaks, constant-time compare
- Integration with existing auth system

**Assessment result**: Complex — multi-file, security-critical auth feature

## Approach
1. Create PasswordResetToken model + migration 005
2. Create Pydantic schemas for request/response
3. Implement service layer (token generation, validation, password update)
4. Add two public endpoints to auth router
5. Write unit tests (schemas, token utils)
6. Write integration tests (full flow)
7. Run quality gates

## Dependencies
- Depends on: RAP-007 (JWT Auth + RBAC) — DONE

## Risks
- Risk: Email delivery not implemented → Mitigation: Use FastAPI BackgroundTasks with a stub/log for V1
- Risk: Migration 005 slot conflict → Mitigation: Develop branch is clean at 004, no conflict
