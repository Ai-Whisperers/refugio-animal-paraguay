# RAP-138 Plan

## Objective
Build a frontend medical alerts and reminders panel that displays overdue, due-today, and upcoming vaccination alerts for shelter staff.

## Description
Staff need a centralized view of animals that have vaccination reminders. The backend `/vaccinations/vaccination-alerts` endpoint already provides structured alert data (overdue, due_today, upcoming). This story creates a frontend panel for the admin dashboard.

## Acceptance Criteria
- [ ] Panel displays overdue vaccinations with animal name and vaccine type
- [ ] Panel displays due-today vaccinations with animal name and vaccine type
- [ ] Panel displays upcoming vaccinations within the next 7 days
- [ ] Alerts are color-coded by severity (red=overdue, yellow=due today, green=upcoming)
- [ ] Empty state shown when no alerts
- [ ] Loading and error states handled

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files
- [x] Change impact ≤10 lines of actual code — exceeds (frontend page is new)
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Simple — new frontend page following established admin patterns

## Approach
1. Create `frontend/src/app/admin/medical/alerts/page.tsx`
2. Add navigation link to admin sidebar
3. Use existing `api` client and auth patterns

## Dependencies
- Backend: `/vaccinations/vaccination-alerts` endpoint (already exists)
- Auth: JWT auth pattern (already implemented)

## Risks
- None significant — follows established patterns
