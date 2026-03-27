# RAP-143 Plan

## Objective
Add a visual recovery timeline page for a surgery that shows all post-op checks with status indicators.

## Description
Staff need to monitor animal recovery after surgery. This page shows a per-surgery timeline of post-op checks fetched from the backend, with metrics (temperature, pain level, appetite, mobility) and concern highlights.

## Acceptance Criteria
- [ ] Staff can navigate to /admin/surgeries/{id}/recovery
- [ ] Page shows surgery summary (type, vet, dates, status, outcome)
- [ ] Page shows all post-op checks in chronological order with status indicators
- [ ] Each check shows: time, checked_by, vital metrics, concerns (highlighted red)
- [ ] Empty state shown when no checks exist
- [ ] Error state shown on API failure
- [ ] "Ver recuperacion" button shown on surgery schedule page for in-progress/completed/complication surgeries

## Complexity Assessment
**Track**: Frontend

**Assessment result**: Simple Fix — pure frontend page, no new backend endpoints needed, uses existing GET /surgeries/{id} and GET /surgeries/{id}/post-op-checks.

## Approach
1. Create /admin/surgeries/[id]/recovery/page.tsx with surgery summary card + timeline
2. Add "Ver recuperacion" button to /admin/surgeries/page.tsx SurgeryRow component
3. Add Cirugias nav item to AdminSidebar

## Dependencies
- Depends on: RAP-142 (surgery schedule page + sidebar entry)

## Risks
- Risk: Backend post-op endpoint may not exist → Mitigation: check existing surgery routes
