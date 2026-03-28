# RAP-504 Plan

## Objective
Implement Google OAuth2 social login so users can authenticate with their Google accounts.

## Description
Add Google OAuth2 authorization code flow to the platform. This enables one-click Google sign-in for adopters and other users, reducing friction in the registration/login process. Includes account linking for users who already have email-based accounts.

## Acceptance Criteria
- [x] Google OAuth2 authorization URL generation (GET /auth/google/start)
- [x] Authorization code exchange and user creation/login (POST /auth/google/callback)
- [x] Account linking flow for existing email-based accounts (POST /auth/google/link, /link/confirm)
- [x] OAuth-only users cannot use password login (redirected to Google)
- [x] Frontend login page with Google OAuth button
- [x] Frontend callback page handles code exchange and account linking
- [x] Database migration adds oauth_provider, oauth_id, profile_picture_url columns
- [x] hashed_password made nullable for OAuth-only users
- [x] CSRF protection via state parameter validation
- [x] Unit tests for service and API layers (21 tests)

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified
- [x] Solution affects <= 3 files — NO (12+ files)
- [ ] Change impact <= 10 lines of actual code
- [ ] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Complex — multi-layer feature spanning backend (migration, model, service, API, schemas, config) and frontend (login page, callback page).

## Approach
1. Database: Add OAuth columns to users table via Alembic migration
2. Config: Add Google OAuth settings (client ID, secret, redirect URI)
3. Service: Create google_oauth_service.py with auth URL, token exchange, user info fetch
4. Schemas: Create Pydantic schemas for OAuth request/response models
5. API: Create google_oauth.py router with start/callback/link/confirm endpoints
6. Auth: Update password login to reject OAuth-only users
7. Frontend: Login page with Google button, callback handler page
8. Tests: Unit tests for service functions and API schema validation

## Dependencies
- Depends on: existing JWT auth system, User model, session service
- Blocked by: none

## Risks
- Risk: In-memory state store not suitable for multi-process production -> Mitigation: documented as TODO, Redis-backed store for production
- Risk: Google API rate limits -> Mitigation: standard OAuth flow with minimal API calls
