---
story: S5
epic: EPIC-76
ticket: RAP-504
title: "Social login (Google OAuth)"
status: in_progress
points: 5
priority: P1
track: Fullstack
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S5: Social login (Google OAuth)

## Story
As a **new user**, I want **to sign in with my Google account** so that **I don't need to remember another password**.

## Description
Implement Google OAuth2 authentication flow. When users first log in with Google, create an account automatically. If email matches existing account, offer to link accounts.

## Acceptance Criteria
- [ ] Login page at /login shows "Continue with Google" button (styled button with Google logo and text)
- [ ] Click "Continue with Google" redirects to Google OAuth consent screen
- [ ] After user consents, Google redirects back to /auth/callback?code=X&state=X
- [ ] Backend exchanges authorization code for access token via Google API
- [ ] Backend extracts user info from Google: email, name, profile picture
- [ ] If user with email exists: ask user if they want to link accounts (show modal "An account with email X already exists. Link with Google?")
- [ ] If user accepts linking: set oauth_provider='google', oauth_id=google_user_id in user record
- [ ] If new email: auto-create user with role='adopter' (default), status='verified' (since Google verified the email), oauth_provider='google', oauth_id=google_user_id, full_name from Google profile, email from Google, profile picture from Google
- [ ] After successful auth: create session/JWT token, redirect to /portal/dashboard
- [ ] Session timeout: 30 days for "Remember me" (if implemented), 1 hour for regular login
- [ ] POST /auth/callback endpoint: accepts code and state, validates state matches session, exchanges code for token, returns user and sets auth cookie
- [ ] GET /auth/google/callback endpoint: handles redirect from Google, calls POST /auth/callback, redirects to dashboard or linking flow
- [ ] Logout removes session/token, clears auth cookie
- [ ] Account linking: user can also link Google to existing account from /portal/profile settings (if account is password-protected)
- [ ] Error handling: if user cancels OAuth consent, redirect to /login with message "Authentication cancelled"
- [ ] Error handling: if OAuth fails, show error message on /login

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test OAuth flow, user creation, account linking logic
- [ ] Integration test: first-time user logs in with Google and account is created
- [ ] Integration test: existing user links Google to their account
- [ ] Integration test: logout clears session properly
- [ ] Security test: CSRF state parameter validated
- [ ] Security test: tokens not exposed in URLs (use POST redirect pattern or auth cookies)
- [ ] Manual testing: Google OAuth flow tested with real Google API (if dev credentials available)
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoints for /auth/google/start, /auth/callback, use google-auth library for token exchange
- Frontend: Login page at pages/login.tsx with Google sign-in button, use Next.js built-in OAuth handling or redirect
- Google OAuth config: CLIENT_ID and CLIENT_SECRET stored in environment variables, REDIRECT_URI must match Google Cloud configuration
- State validation: generate random state, store in session, validate on callback to prevent CSRF
- Token handling: use httpOnly secure cookies for session tokens, or JWT in Authorization header
- User creation: when auto-creating from Google, set: full_name, email, profile_picture_url (from Google), oauth_provider, oauth_id, role='adopter', status='verified'
- Account linking: store oauth_provider and oauth_id in users table, allow multiple providers per user
- Email verification: skip for Google accounts (already verified by Google)
- Profile picture: download from Google URL on auth, store in cloud storage, reference from profile_picture_url column

## Story Points: 5
