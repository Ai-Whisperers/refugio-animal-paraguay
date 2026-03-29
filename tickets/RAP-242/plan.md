# RAP-242 Plan

## Objective
Add zero-downtime JWT key rotation: support a previous secret key during the transition window so in-flight tokens remain valid after a key change.

## Acceptance Criteria
- [x] Settings.secret_key_previous field added with length validation
- [x] decode_access_token falls back to previous key on failure
- [x] Auth dependencies pass previous key to decode_access_token
- [x] Admin endpoint GET /admin/security/jwt-rotation-status shows rotation state
- [x] Keys are masked in API responses (first 8 chars only)
- [x] Unit tests cover all rotation scenarios

## Complexity Assessment
**Track**: Simple Fix — 4 files changed, all auth-layer changes with no DB impact.

## Approach
1. Add secret_key_previous to Settings with validator
2. Update decode_access_token to try previous key on failure
3. Pass previous key in auth/dependencies.py
4. Add admin_security.py router with rotation status endpoint
5. Write 18 unit tests
