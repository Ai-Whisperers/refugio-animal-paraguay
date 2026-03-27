---
story: S4
epic: EPIC-76
ticket: RAP-503
title: "Profile management page"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S4: Profile management page

## Story
As a **logged-in user**, I want **to manage my profile information and preferences** so that **I can keep my details current and control how I receive notifications**.

## Description
Create a profile management page where users can edit personal information, change password, set notification preferences, and access GDPR data export/deletion options.

## Acceptance Criteria
- [ ] Profile page exists at /portal/profile, requires authentication
- [ ] Page has 3 tabs: "Personal Info", "Password & Security", "Preferences"
- [ ] Personal Info tab: form with fields: full_name (editable text), email (read-only display), phone (editable text, with +595 format), address (editable textarea), city/region dropdown, profile photo upload (image field)
- [ ] Personal Info save: PUT /api/users/profile endpoint, validates phone format, validates address length (max 500 chars), returns updated user data
- [ ] Personal Info confirmation: "Changes saved successfully" message after save
- [ ] Password & Security tab: form with fields: current_password (password field, required), new_password (password field with strength indicator), confirm_password (password field), "Change Password" button
- [ ] Password change: POST /api/users/change-password endpoint, validates current password is correct, validates new password meets strength requirements (min 8 chars, 1 uppercase, 1 number, 1 special), checks new password != current password, hashes new password with bcrypt cost 12
- [ ] Password change confirmation: requires email confirmation link sent to user's email (user must click link in email to complete change)
- [ ] Preferences tab: checkboxes for notification settings: "Email notifications for adoption updates" (checkbox), "Email notifications for donation updates" (checkbox), "Email notifications for volunteer shifts" (checkbox), "WhatsApp notifications" (checkbox), "In-app notifications" (checkbox)
- [ ] Preferences save: PUT /api/users/preferences endpoint, stores notification preferences, returns confirmation
- [ ] Preferences tab also includes: "Download my data" button (GDPR), "Delete my account" button (GDPR with confirmation modal)
- [ ] Download data: GET /api/users/gdpr/export endpoint, returns JSON file containing all user data (profile, applications, donations, animals, etc.) formatted as downloadable JSON, file named "refugio_data_YYYY-MM-DD.json"
- [ ] Delete account: POST /api/users/gdpr/delete endpoint with confirmation token from email, requires password re-entry, soft-deletes user and anonymizes all personal data, unlinks donations, applications, foster animals
- [ ] Delete confirmation email: sent before deletion is finalized, contains 24-hour link to confirm deletion
- [ ] All changes require fresh authentication (session should prompt re-login for security-sensitive operations)
- [ ] Form validation: client-side real-time, server-side validation on all endpoints

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test profile update, password change validation, preferences save, GDPR export format
- [ ] Integration test: update profile info and verify changes persisted
- [ ] Integration test: change password flow works end-to-end with email confirmation
- [ ] Integration test: toggle notification preferences and verify saved
- [ ] Integration test: GDPR export generates valid JSON with all user data
- [ ] Integration test: delete account flow works and user data is anonymized
- [ ] Component test: all form tabs display and are interactive
- [ ] Security test: password changes require current password verification
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoints for PUT /api/users/profile, POST /api/users/change-password, PUT /api/users/preferences, GET /api/users/gdpr/export, POST /api/users/gdpr/delete
- Frontend: React page at pages/portal/profile.tsx with tabbed layout (Personal Info, Password, Preferences)
- Password change flow: send confirmation email with token, token stored in password_change_tokens table (24h expiry), user clicks link to verify
- GDPR data export: query all relevant tables (users, applications, donations, animals, etc.), return as JSON
- GDPR deletion: soft delete user (deleted_at timestamp), anonymize columns (name -> 'Deleted User', email -> 'deleted+{uuid}@refugio.local', phone -> null), keep audit trail
- Photo upload: store in cloud storage (S3/similar), validate file type (JPEG/PNG), max 5MB, store path in user_profile.photo_url
- Notification preferences stored in user_preferences table with columns: email_adoption, email_donations, email_volunteer, whatsapp_enabled, inapp_enabled

## Story Points: 5
