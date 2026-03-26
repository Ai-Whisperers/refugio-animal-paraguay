# RAP-037 Plan

## Objective
Add animal sponsorship tiers (Bronze/Silver/Gold) with recurring Stripe subscriptions for EU and international donors.

## Description
Donors can sponsor a specific animal at Bronze ($10/mo), Silver ($25/mo), or Gold ($50/mo) tiers. This creates a Stripe Subscription for recurring billing. The backend manages the sponsorship lifecycle: create, pause, resume, cancel, and tier changes. Frontend/dashboard work is deferred to a frontend sprint.

## Acceptance Criteria
- [ ] Sponsorship model with tier enum (bronze, silver, gold) and status lifecycle
- [ ] Alembic migration for sponsorships table
- [ ] Stripe Subscription integration for recurring billing
- [ ] POST /sponsorships endpoint to create a sponsorship
- [ ] GET /donors/{id}/sponsorships endpoint to list donor's sponsorships
- [ ] GET /animals/{id}/sponsors endpoint to list animal's sponsors
- [ ] PATCH /sponsorships/{id} to change tier, pause, resume
- [ ] DELETE /sponsorships/{id} to cancel
- [ ] Webhook handling for subscription lifecycle events
- [ ] Unit and integration tests with 80%+ coverage

## Complexity Assessment
**Track**: Complex Implementation

- Multiple files (model, migration, service, schemas, API, webhooks, tests)
- Stripe Subscriptions API integration
- Lifecycle state machine (active, paused, cancelled, past_due)

**Assessment result**: Complex — multi-file, Stripe subscription integration, state machine

## Approach
1. Create Sponsorship model + SponsorshipTier enum + migration
2. Create Pydantic schemas (request/response)
3. Implement sponsorship service (Stripe Subscription CRUD)
4. Add API endpoints with staff auth
5. Extend webhook handler for subscription events
6. Write unit + integration tests

## Dependencies
- Depends on: Donor model (EPIC-3), Animal model (EPIC-1), Stripe foundation (RAP-009), Auth (RAP-007)
- All dependencies met

## Risks
- Risk: Stripe Subscription API complexity → Mitigation: Mock in tests, focus on core lifecycle
