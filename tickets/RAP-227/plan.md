# RAP-227 Plan

## Objective
Implement user self-service GDPR account deletion request in the frontend portal profile page.

## Description
The backend already has `POST /portal/gdpr/delete` (request with password) and `POST /portal/gdpr/delete/confirm` (confirm via token). The frontend only has a placeholder button with `window.confirm()`. This story wires the frontend to the real API: adds a confirmation modal, calls the API, shows success state, and creates a `/portal/gdpr/confirm-deletion` page to handle the email confirmation link.

## Acceptance Criteria
- [ ] "Solicitar eliminacion" button opens a confirmation modal (not `window.confirm()`)
- [ ] Modal requires password re-entry before submitting
- [ ] On success, shows "check your email" message
- [ ] Separate page `/portal/gdpr/confirm-deletion?token=...` processes the confirmation token
- [ ] Confirmation page shows success/error state and redirects to login on success
- [ ] All edge cases handled (wrong password, expired token, network error)
- [ ] Unit and integration tests passing

## Complexity Assessment
**Track**: Simple Fix — 1 modified file + 1 new page, limited scope, well-understood pattern

**Assessment result**: Simple Fix — frontend only, extends existing pattern

## Approach
1. Modify `frontend/src/app/portal/profile/page.tsx` — replace `window.confirm()` with a proper modal
2. Create `frontend/src/app/portal/gdpr/confirm-deletion/page.tsx` — token confirmation page

## Dependencies
- Depends on: RAP-225 (S1 Data deletion API — DONE), RAP-226 (S2 Third-party cascade — DONE)

## Risks
- Risk: Confirmation email might reference a frontend URL — need to check how profile_service builds the email link → Mitigation: service uses `request_account_deletion()` which returns a token; the email URL needs to match our new page path
