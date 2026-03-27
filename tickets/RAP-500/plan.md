# RAP-500 Plan

## Objective
Enable public self-registration for adopters, donors, volunteers, and foster carers.

## Acceptance Criteria
- [x] POST /auth/register endpoint with full_name, email, phone, password, role
- [x] Email validation (rejects invalid formats, rejects duplicates)
- [x] Phone validation (+595 Paraguay format, rejects duplicates)
- [x] Password strength (8+ chars, 1 uppercase, 1 digit, 1 special)
- [x] Role selection (adopter, donor, volunteer, foster only)
- [x] User created with status='unverified'
- [x] Next.js registration page at /register with form validation
- [x] Client-side validation with password strength indicator
- [x] Loading state prevents double-submission
- [x] Database migration adds full_name, phone columns and new roles

## Complexity Assessment
**Track**: Complex — Fullstack (backend API + DB migration + frontend page + tests)

## Approach
1. DB migration: add full_name, phone columns, extend role constraint
2. Update User model with new fields and roles
3. Create registration schema with validators
4. Create public registration endpoint
5. Create Next.js registration page
6. Write unit and integration tests
