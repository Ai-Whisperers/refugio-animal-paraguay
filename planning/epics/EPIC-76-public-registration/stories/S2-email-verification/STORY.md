---
story: S2
epic: EPIC-76
ticket: RAP-501
title: "Email verification flow with token"
status: done
points: 3
priority: P0
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S2: Email verification flow with token

## Story
As a **system**, I want **to send verification emails with secure tokens** so that **users must verify they own the email address before using the account**.

## Description
Implement a complete email verification flow where users receive a token-based verification link. Tokens must be cryptographically secure, time-limited (24 hours), and single-use.

## Acceptance Criteria
- [ ] Verification token generation: UUID format, unique per user, 24-hour expiry
- [ ] GET /auth/verify-email?token=X endpoint: validates token format (UUID), checks token not expired, checks token not already used, validates token belongs to exact user_id in token payload
- [ ] Token validation logic: token must be valid UUID, must exist in database, must not have used_at timestamp, must be within 24 hours of created_at
- [ ] Upon successful verification: set user status to 'verified', set token used_at timestamp, return HTTP 200 with success message
- [ ] Upon expired token (>24 hours): return HTTP 400 with error code 'token_expired', include resend link in error response
- [ ] Upon invalid token format: return HTTP 400 with error code 'invalid_token'
- [ ] Upon already-used token: return HTTP 400 with error code 'token_already_used', suggest requesting new token
- [ ] POST /auth/resend-verification-email endpoint: accepts email, rate limit 3 requests per hour per email, generates new token, sends new verification email
- [ ] Rate limiting returns HTTP 429 with Retry-After header if limit exceeded
- [ ] Verification email contains: user's name, "Click here to verify" link with full URL (https://domain/auth/verify?token=X), 24-hour expiry statement, resend link (https://domain/auth/resend?email=X)
- [ ] Email template is HTML formatted, mobile-responsive, includes Refugio branding
- [ ] Unverified users cannot access /portal/* pages (redirect to /auth/verify-pending)
- [ ] Database: email_verification_tokens table with columns: id (UUID PK), user_id (FK), token (UUID UNIQUE), created_at, expires_at (calculated as created_at + 24h), used_at (nullable)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test token generation, expiry checking, used token detection, rate limiting
- [ ] Integration test: user registers, receives email, clicks link, account becomes verified
- [ ] Integration test: resend verification email after first expires
- [ ] Integration test: expired token returns correct error
- [ ] Integration test: used token returns correct error
- [ ] Email sending tested with mock (verify email body contains correct link and token)
- [ ] Deployed to staging and verified: end-to-end email verification works

## Technical Notes
- Backend: FastAPI endpoints for /auth/verify-email and /auth/resend-verification-email
- Token generation: uuid.uuid4() converted to string
- Rate limiting: Use Redis with key pattern: "resend_email:{email}:{date}" with 3-request limit per hour
- Email service: Use existing email provider (Mailgun/SendGrid/etc), or mock in development
- Database migration: Create email_verification_tokens table with proper indexes on user_id and token columns
- Security: Never expose user_id in URL, only token. Tokens should not be guessable.
- Verification email sent immediately upon user registration
- No resend link shown to already-verified users
- Include user's name in verification email greeting

## Story Points: 3
