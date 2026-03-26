# RAP-071 Plan

## Objective
Implement animal sponsorship tiers (Bronze/Silver/Gold) with Stripe recurring subscription management and a sponsor dashboard API.

## Description
Donors can sponsor a specific animal at monthly price tiers. Bronze ($10/month), Silver ($25/month), and Gold ($50/month). Sponsorships are backed by Stripe Subscriptions for recurring billing. Staff and sponsors can view and manage (pause, cancel, upgrade) subscriptions.

## Acceptance Criteria
- [ ] SponsorshipTier model with Bronze/Silver/Gold tiers and correct pricing
- [ ] Sponsorship model linked to donor and animal with Stripe subscription ID
- [ ] POST /sponsorships — create sponsorship with Stripe subscription
- [ ] GET /sponsorships — list all sponsorships (staff)
- [ ] GET /sponsorships/{id} — single sponsorship (staff or sponsor owner)
- [ ] PATCH /sponsorships/{id}/cancel — cancel sponsorship (donor or staff)
- [ ] PATCH /sponsorships/{id}/pause — pause sponsorship (donor or staff)
- [ ] PATCH /sponsorships/{id}/resume — resume sponsorship (donor or staff)
- [ ] GET /animals/{id}/sponsorships — sponsorships for a specific animal (staff)
- [ ] GET /donors/{id}/sponsorships — all sponsorships for a donor (staff or donor)
- [ ] Alembic migration for sponsorship_tiers and sponsorships tables
- [ ] Unit tests: sponsorship creation, status transitions, tier validation
- [ ] Integration tests: full CRUD API including Stripe mock

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — requires Stripe Subscriptions API, new models (2 tables), 10+ endpoints, 85%+ coverage requirement.

## Approach
1. Add SponsorshipTier and Sponsorship ORM models
2. Create Alembic migration (revision 014)
3. Add Pydantic schemas
4. Implement API router at /sponsorships
5. Register router in app.py
6. Write unit tests (pure logic: tier validation, status transitions)
7. Write integration tests (API endpoints with mocked Stripe)

## Dependencies
- Depends on: EPIC-3 (Stripe foundation — already in place at RAP-009)
- Depends on: EPIC-1 (Animal model — already in place)
- Depends on: EPIC-10 (Auth/JWT — already in place)

## Risks
- Risk: Stripe Subscription API changes → Mitigation: Mock Stripe in tests, use env var key check
- Risk: Complex status machine → Mitigation: Clear enum with documented transitions
