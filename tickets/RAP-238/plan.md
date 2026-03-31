# RAP-238 Plan

## Objective
Enforce two-factor authentication at login for all accounts that have TOTP enabled.

## Description
When a user has `totp_enabled=True`, the `/auth/token` login endpoint must reject
authentication unless a valid TOTP code or a valid backup code is supplied via the
optional `totp_code` form field. This closes the gap where 2FA could be bypassed by
simply not providing the second factor.

## Acceptance Criteria
- [x] Login without `totp_code` returns HTTP 401 with `detail="totp_required"` when 2FA is enabled
- [x] Login with a valid live TOTP code succeeds
- [x] Login with a valid unused backup code succeeds (and marks it used)
- [x] Login with an incorrect code returns HTTP 401
- [x] Integration tests cover all four branches

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified — login endpoint had no 2FA gate
- [x] Solution affects ≤3 files — only `src/api/auth.py` + test file
- [x] Change impact ≤10 lines of actual code — ~15 lines in auth.py
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Simple Fix — narrow change to login endpoint only

## Approach
Add 2FA enforcement block after password verification in the `/auth/token` handler.
Try TOTP first; fall back to backup code service.

## Dependencies
- Depends on: RAP-235 (TOTP service), RAP-237 (backup code service)
- Blocked by: none
