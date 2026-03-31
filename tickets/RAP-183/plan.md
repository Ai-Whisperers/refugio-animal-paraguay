# RAP-183 Plan

## Objective
Staff can mark volunteers as attended or no-show for completed shifts, and view attendance records per shift.

## Description
After a shift occurs, staff mark each signed-up volunteer as attended (true) or no-show (false).
Frontend: attendance management in the admin shift detail view (modal or inline in shift card).
Backend: PATCH endpoint for staff to set the attended flag, GET endpoint for all signups on a shift.

## Acceptance Criteria
- [ ] GET /api/shifts/{id}/signups returns all signups for a shift (staff only)
- [ ] PATCH /api/shifts/{id}/signups/{signup_id} updates attended flag (staff only)
- [ ] attended=true marks attendance, attended=false marks no-show, attended=null clears
- [ ] Only works for shifts that are completed or past their shift_date
- [ ] Admin shift detail page shows signup list with attended/no-show controls
- [ ] Unit tests for attendance update schema
- [ ] Integration tests for happy path + edge cases

## Complexity Assessment
**Track**: Complex — backend endpoint + frontend admin UI

## Approach
1. Add GET /api/shifts/{id}/signups and PATCH /api/shifts/{id}/signups/{signup_id}
2. Add ShiftSignupListResponse and AttendanceUpdateRequest schemas
3. Add admin shift detail page at /admin/shifts/[id]/page.tsx
4. Unit tests + integration tests

## Dependencies
- Depends on: RAP-180 (shift model) ✓, RAP-182 (ShiftSignup model) ✓

## Risks
- None significant
