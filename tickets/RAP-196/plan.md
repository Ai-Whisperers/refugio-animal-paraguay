# RAP-196 Plan

## Objective
Add a volunteer leaderboard endpoint and admin frontend page showing top volunteers by approved hours.

## Description
EPIC-40 S2 — builds on the hours logging API (RAP-195) to surface a ranked view of volunteer contributions. Staff can see which volunteers have logged the most approved hours, filtered by time period.

## Acceptance Criteria
- [ ] Backend: GET /api/staff/volunteer-hours/leaderboard returns ranked list with volunteer name, approved hours, category breakdown
- [ ] Endpoint supports period filter (all, month, quarter, year) and limit (1-50)
- [ ] Frontend: /admin/volunteers/leaderboard page shows ranked table with volunteer details
- [ ] Empty state handled (no hours logged)
- [ ] Unit tests cover response schema and period logic
- [ ] Integration tests cover leaderboard endpoint

## Complexity Assessment
**Track**: Complex (fullstack)
**Assessment**: 3 files changed — volunteer_hours.py (new endpoint), api.ts (new types), leaderboard/page.tsx (new frontend page)

## Approach
1. Add leaderboard response schema and GET endpoint to staff_router in volunteer_hours.py
2. Join volunteer_hours_log → volunteer_profiles → users for name resolution
3. Add LeaderboardEntry type to frontend/src/types/api.ts
4. Create frontend page at /admin/volunteers/leaderboard/page.tsx

## Dependencies
- Depends on: RAP-195 (volunteer_hours_log model + API)

## Risks
- Risk: test DB missing volunteer_profiles table → Integration tests will fail same as RAP-195; document as pre-existing
