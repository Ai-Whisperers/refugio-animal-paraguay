# RAP-194 Plan

## Objective
Implement foster supply request and tracking so foster families can request supplies from the shelter and staff can manage fulfillment.

## Description
Foster families often need supplies (food, medicine, bedding, toys) during an animal's placement. This feature provides a simple request/fulfillment loop: foster families submit requests, staff review and fulfill them, and both parties can track status. This reduces coordination overhead and ensures no supply request falls through the cracks.

## Acceptance Criteria
- [ ] FosterSupplyRequest ORM model with status lifecycle (pending → approved/rejected → fulfilled)
- [ ] Alembic migration for foster_supply_requests table
- [ ] POST /api/foster/supply-requests — foster family submits request (authenticated)
- [ ] GET /api/foster/supply-requests/me — foster family views own requests (authenticated)
- [ ] GET /api/staff/foster/supply-requests — staff lists all requests with status filter (staff only)
- [ ] PUT /api/staff/foster/supply-requests/{id}/fulfill — mark fulfilled (staff only)
- [ ] PUT /api/staff/foster/supply-requests/{id}/reject — reject with reason (staff only)
- [ ] Admin UI page at /admin/foster/supply-requests showing requests table
- [ ] Unit tests for supply request service logic
- [ ] Integration tests for the endpoints

## Complexity Assessment
**Track**: Complex — new model, migration, API + frontend

**Assessment result**: Complex — multiple files, DB change required

## Approach
1. Create FosterSupplyRequest model
2. Create migration 078_create_foster_supply_requests_table.py
3. Add service functions in foster_supply_service.py
4. Add endpoints to foster.py (public_router + staff_router)
5. Create frontend admin page
6. Write unit and integration tests

## Dependencies
- Depends on: RAP-190 (FosterProfile exists)
