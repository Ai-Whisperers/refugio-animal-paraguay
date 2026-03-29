# RAP-182 Plan

## Objective
Enable volunteers to self-signup for open shifts and view/cancel their own shift registrations.

## Description
Volunteers can browse available shifts and register themselves. The system prevents double-signup,
respects shift capacity limits, and updates slot counts automatically. Frontend page lives at
`/volunteer/shifts`.

## Acceptance Criteria
- [ ] Volunteer can POST /api/shifts/{id}/signup to join an open shift
- [ ] Signup blocked if shift is full, cancelled, or completed
- [ ] Signup blocked if volunteer already signed up (returns 409)
- [ ] Volunteer can DELETE /api/shifts/{id}/signup to cancel their own signup
- [ ] GET /api/shifts/my-signups returns authenticated volunteer's signups
- [ ] slots_filled increments on signup, decrements on cancel
- [ ] Shift status auto-transitions open↔full when capacity reached
- [ ] Frontend `/volunteer/shifts` page shows open shifts and signup state
- [ ] Unit and integration tests passing

## Complexity Assessment
**Track**: Complex — multiple backend endpoints + frontend page + state transitions

## Approach
1. Add signup endpoints to shifts.py (POST signup, DELETE signup, GET my-signups)
2. Register new routes in main app
3. Add TypeScript types for ShiftSignup
4. Build `/volunteer/shifts` frontend page
5. Unit tests for new endpoints
6. Integration tests for happy path + edge cases

## Dependencies
- Depends on: RAP-180 (shift model + base API) ✓ DONE
- Blocked by: None

## Risks
- Risk: slots_filled race condition → Mitigation: Use DB-level increment with check constraint
