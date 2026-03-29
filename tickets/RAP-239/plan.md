# RAP-239 Plan

## Objective
Provide a complete 2FA recovery flow: fresh backup code regeneration and an admin reset
endpoint that unblocks staff who have lost all their 2FA credentials.

## Description
Users who exhaust their backup codes or lose their TOTP device need a recovery path.
This story adds two mechanisms: self-service backup code regeneration (authenticated)
and an admin-only hard reset that disables 2FA + clears all codes for a target user.
The frontend security settings page is extended with the regeneration UI.

## Acceptance Criteria
- [x] `POST /auth/2fa/backup-codes` regenerates a fresh batch and returns plain codes
- [x] `DELETE /auth/2fa/admin/users/{user_id}` resets 2FA for a user (admin only)
- [x] Admin reset clears TOTP secret, disables 2FA, and deletes all backup codes
- [x] Non-admin staff receive HTTP 403 on the admin endpoint
- [x] Admin reset of a non-existent user returns HTTP 404
- [x] Frontend security settings page shows backup code count and regeneration button
- [x] Integration tests cover all admin reset scenarios

## Complexity Assessment
**Track**: Complex — two endpoints, frontend component, depends on backup code service

**Assessment result**: Complex — 3 files changed but spans backend + frontend

## Approach
Backend: Add `generate_new_backup_codes` endpoint to `two_factor.py` + admin reset
endpoint. Frontend: Extend security settings page with backup code count display and
regenerate button.

## Dependencies
- Depends on: RAP-237 (backup_code_service), RAP-238 (2FA enforcement)
- Blocked by: none
