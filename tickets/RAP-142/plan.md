# RAP-142 Plan

## Objective
Add a surgery scheduling interface page to the admin panel showing all scheduled surgeries by date with animal context.

## Description
Staff need to view all surgeries across all animals in a calendar/list view sorted by scheduled date. This requires a new backend endpoint listing all surgeries with animal name context, and a frontend page with filters.

## Acceptance Criteria
- [ ] Surgery schedule page shows all surgeries with date, animal name, procedure type, and status
- [ ] Surgeries are sorted by scheduled date
- [ ] Status filter (scheduled/in_progress/completed/cancelled)
- [ ] Backend `GET /surgeries` endpoint returns paginated list with animal name
- [ ] AdminSidebar includes Surgery Schedule link
- [ ] Empty state handled
- [ ] Error state handled

## Complexity Assessment
**Track**: Fullstack (small backend addition + Frontend)

**Assessment result**: Complex — adds new backend endpoint, new frontend page, sidebar update, types.

## Approach
1. Add `SurgeryWithAnimalName` response schema to backend
2. Add `GET /surgeries` endpoint with date/status filters
3. Add Surgery types to frontend api.ts
4. Create `/admin/surgeries/page.tsx`
5. Update AdminSidebar to include link
6. Write backend + frontend tests

## Dependencies
- Depends on: RAP-140 (Surgery record model and API) — DONE
- Depends on: RAP-141 (Post-op monitoring) — DONE

## Risks
- Risk: Animal name join may be complex → Mitigation: Simple JOIN query on animal_id
