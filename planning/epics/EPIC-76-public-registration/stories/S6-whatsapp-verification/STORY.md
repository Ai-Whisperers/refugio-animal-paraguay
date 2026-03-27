---
story: S6
epic: EPIC-76
ticket: RAP-505
title: "WhatsApp-based phone verification"
status: done
points: 5
priority: P2
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S6: WhatsApp-based phone verification

## Story
As a **user with a phone number**, I want **to verify my phone via WhatsApp** so that **I can enable WhatsApp notifications and ensure my phone number is valid**.

## Description
Send a 6-digit OTP (one-time password) via WhatsApp to users' registered phone numbers. Users enter the OTP to verify their phone and enable WhatsApp notifications.

## Acceptance Criteria
- [ ] POST /auth/verify-phone/send-otp endpoint: accepts phone number in +595XXXXXXXXX format (international), generates random 6-digit OTP, stores OTP in database with 5-minute expiry, sends OTP via WhatsApp using Twilio
- [ ] OTP generation: cryptographically random 6 digits (000000-999999), unique per phone per request
- [ ] OTP storage: phone_verification_otps table with columns: id (UUID PK), user_id (FK, nullable for pre-auth), phone (string), otp_hash (hashed OTP), created_at, expires_at (created_at + 5 min), attempted_count (int, default 0), verified_at (nullable)
- [ ] WhatsApp message format: "Your Refugio verification code is: XXXXXX. Valid for 5 minutes. Do not share this code."
- [ ] Rate limiting: max 3 OTP send requests per phone number per hour, returns HTTP 429 if exceeded with Retry-After header
- [ ] POST /auth/verify-phone/verify-otp endpoint: accepts phone and otp_code (string), validates OTP is not expired, validates OTP matches (constant-time comparison), validates not already verified, validates attempted_count < 5
- [ ] Failed OTP attempt: increment attempted_count, return HTTP 400 with error "Invalid OTP"
- [ ] Fifth failed attempt: lock OTP record, require new OTP request, return HTTP 429 "Too many attempts, please request a new code"
- [ ] Successful OTP verification: set verified_at timestamp, update user phone_verified=true and phone_verified_at=now(), return HTTP 200 with success message
- [ ] Expired OTP (>5 minutes): return HTTP 400 with error code 'otp_expired', include "Request new code" link
- [ ] GET /auth/verify-phone/status?phone=... endpoint: returns {verified: bool, verified_at: datetime|null} for checking verification status
- [ ] Unverified phone shows badge in profile
- [ ] Verified phone enables WhatsApp notification toggle in preferences
- [ ] Phone number can only be verified once (subsequent verifications update existing record)
- [ ] Support re-requesting OTP: new OTP invalidates previous OTP

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test OTP generation, expiry, rate limiting, hashing, attempt counting
- [ ] Integration test: send OTP and verify with correct code
- [ ] Integration test: verify fails with incorrect OTP
- [ ] Integration test: rate limiting enforced after 3 sends per hour
- [ ] Integration test: attempt counting enforced, locks after 5 failures
- [ ] Integration test: expired OTP returns correct error
- [ ] Mock WhatsApp provider for testing: verify message format and phone number
- [ ] Security test: OTP stored as hash (bcrypt), never logged or exposed
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoints for /auth/verify-phone/send-otp, /auth/verify-phone/verify-otp, /auth/verify-phone/status
- WhatsApp provider: Use Twilio Messaging API with WhatsApp channel
- OTP hashing: bcrypt with cost factor 12, always use constant-time comparison (hmac.compare_digest)
- Rate limiting: Redis key pattern "otp_send:{phone}:{date_hour}" with 3-request limit per hour
- Attempt limiting: Redis key pattern "otp_attempts:{phone}:{otp_id}" with 5-attempt limit
- Database migration: Create phone_verification_otps table with indexes on user_id, phone, created_at
- Error messages: "Invalid OTP", "OTP expired", "Too many attempts", "Invalid phone format"
- Twilio credentials: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM stored in environment
- Phone format validation: accept +595 with 9 digits (Paraguay), reject other formats
- OTP validity: 5 minutes from creation

## Story Points: 5
