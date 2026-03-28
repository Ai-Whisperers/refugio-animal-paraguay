# RAP-192 Plan

## Objective
Implement foster check-in schedule and reminders so staff can track welfare of animals in foster care.

## Description
Foster families need periodic check-ins to ensure animals are being cared for properly.
Staff schedule check-ins at regular intervals (e.g. weekly), log results, and the system
tracks upcoming and overdue check-ins. Manual reminder dispatch is also supported.

## Acceptance Criteria
- [ ] Staff can schedule a check-in for an active foster placement
- [ ] Staff can list all check-ins for a placement (upcoming, completed, missed)
- [ ] Staff can complete a check-in with notes
- [ ] Staff can view a dashboard of all upcoming/overdue check-ins across all placements
- [ ] API endpoints documented in OpenAPI schema
- [ ] Unit and integration tests passing (80%+ coverage)

## Complexity Assessment
**Track**: Complex Implementation

### Complex criteria met:
- New DB model (foster_check_ins) + migration
- New service layer
- New API endpoints added to existing foster router
- Frontend dashboard component
- Multiple edge cases (no active placement, already completed, etc.)

**Assessment result**: Complex — new model, service, and multiple endpoints

## Approach
1. DB model: `FosterCheckIn` with status machine (pending → completed/missed/cancelled)
2. Alembic migration 077
3. Service: CRUD + upcoming check-ins query
4. API: 5 endpoints on `staff_router` in foster.py
5. Tests: unit (service) + integration (API)
6. Frontend: `/staff/foster/check-ins` page listing upcoming check-ins

## Dependencies
- Depends on: RAP-191 (foster placements) — DONE (PR #317)

## Risks
- Risk: Check-in reminder delivery requires email/WhatsApp service → Mitigation: log reminder dispatch, skip actual delivery (out of scope)
