# RAP-019 Plan

## Objective
Add in-kind donation recording to track non-cash contributions (food, supplies, vet services) with estimated values.

## Description
Shelter staff frequently receive non-cash donations that need tracking alongside monetary donations. This extends the donation system with an InKindDonation model, CRUD API endpoints, and a donor summary endpoint that combines cash + in-kind totals. The item_type enum covers common shelter donation categories.

## Acceptance Criteria
- [ ] InKindDonation model with item_type enum, quantity, estimated_value_cents, currency, notes
- [ ] Alembic migration creates in_kind_donations table with proper constraints
- [ ] CRUD endpoints: POST, GET list (filtered), GET single, PUT, DELETE
- [ ] Donor giving summary endpoint returns combined cash + in-kind totals
- [ ] Staff-only access on all endpoints
- [ ] No negative estimated_value_cents allowed (DB + schema validation)
- [ ] Unit tests for model, schemas, enum values
- [ ] Integration tests for full CRUD and donor summary
- [ ] 80%+ coverage on new code

## Complexity Assessment
**Track**: Complex Implementation

- Multiple files: model, migration, schemas, API, tests
- New enum, new table, new relationships
- Donor summary aggregation query

**Assessment result**: Complex — new model + migration + full CRUD + aggregation endpoint

## Approach
1. Create InKindDonation model with ItemType enum in donation.py
2. Create Alembic migration for in_kind_donations table
3. Add Pydantic schemas for create/update/response
4. Build API endpoints (staff-only CRUD + donor summary)
5. Write unit tests (model, schemas)
6. Write integration tests (CRUD, filters, donor summary)
7. Run all quality gates

## Dependencies
- Depends on: RAP-009 (Stripe foundation — Donor model exists)
- No blockers

## Risks
- Risk: Migration conflict with unmerged branches → Mitigation: Use next available migration number on develop
