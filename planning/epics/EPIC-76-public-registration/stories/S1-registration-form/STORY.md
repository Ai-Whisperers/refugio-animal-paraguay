---
story: S1
epic: EPIC-76
ticket: RAP-500
title: "Self-registration form"
status: ready
points: 5
priority: P0
track: Fullstack
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S1: Self-registration form

## Story
As a **new user**, I want **to register myself with name, email, phone, password, and role** so that **I can access the platform and use it for adoption, donation, volunteering, or fostering**.

## Description
Create a public registration form and API endpoint that allows users to self-register. The form should collect essential information including name, email, phone, password, and role selection. All inputs must be validated on both client and server side.

## Acceptance Criteria
- [ ] POST /auth/register endpoint exists and accepts JSON payload with: full_name (string, 2-100 chars), email (valid format), phone (valid format), password (min 8 chars, 1 uppercase, 1 number, 1 special char), role (enum: adopter|donor|volunteer|foster)
- [ ] Email validation: rejects invalid formats, rejects if email already registered
- [ ] Phone validation: accepts +595 format (Paraguay), rejects if phone already registered
- [ ] Password strength check: minimum 8 characters, requires 1 uppercase letter, 1 number, 1 special character, error messages for each requirement
- [ ] Role selection: dropdown with exactly these 4 options: adopter, donor, volunteer, foster (users can add more roles later)
- [ ] User created in database with status='unverified' upon successful registration
- [ ] Response returns user_id, email confirmation message, and expected next step
- [ ] Next.js registration page exists at /register with form fields: Full Name, Email, Phone (with +595 placeholder), Password (with strength indicator), Confirm Password, Role dropdown, Register button
- [ ] Client-side validation: real-time email/phone format check, password strength meter, error messages displayed inline
- [ ] Form prevents double-submission with loading state on button
- [ ] Successful registration shows confirmation message and prompts for email verification
- [ ] Duplicate email/phone error returns HTTP 400 with specific error code
- [ ] Database migration creates users table (if not existing) with required columns

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test valid/invalid emails, phone formats, password requirements, duplicate detection, all 4 roles
- [ ] Integration test: register user with all required fields and verify user created in DB with unverified status
- [ ] Edge cases handled: very long names, special characters in names, leading/trailing whitespace trimmed
- [ ] Error responses: clear messages for duplicate email, invalid phone format, weak password
- [ ] Deployed to staging and verified: registration flow works end-to-end

## Technical Notes
- Backend: FastAPI endpoint at POST /auth/register, use Pydantic model for validation
- Frontend: React form component at pages/register.tsx, use React Hook Form for form state management
- Database: Users table must have columns: id (UUID PK), full_name, email (UNIQUE), phone (UNIQUE), password_hash, role, status ('unverified'|'verified'), created_at, updated_at
- Validation: email regex from RFC 5322, phone format validation for +595XXXXXXXXX (9 digits after country code)
- Password hashing: bcrypt with cost factor 12
- Response format: {"user_id": "uuid", "message": "Registration successful. Check your email for verification link.", "next_step": "verify_email"}

## Story Points: 5
