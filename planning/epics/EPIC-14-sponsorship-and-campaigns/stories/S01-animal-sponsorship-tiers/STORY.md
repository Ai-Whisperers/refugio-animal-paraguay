---
story: S01
epic: EPIC-14
title: Animal Sponsorship Tiers
status: ready
created: 2026-03-26T00:00:00.000000
effort: 8
---

# S01: Animal Sponsorship Tiers

## User Story

As a **donor**, I want to **sponsor a specific animal at different monthly or annual price tiers (Bronze/Silver/Gold)** so that **I can financially support an animal I care about and receive updates about their progress**.

## Acceptance Criteria

**Given** I am viewing an adoptable animal's page
**When** I see sponsorship options
**Then** I can choose Bronze ($10/month), Silver ($25/month), or Gold ($50/month) recurring sponsorship

**Given** I select a sponsorship tier and proceed to payment
**When** I complete the Stripe checkout for recurring donation
**Then** my sponsorship is created with the animal and I receive a confirmation email

**Given** my sponsorship is active
**When** I log in to my account
**Then** I can see my sponsored animal, current tier, and manage my subscription (pause, upgrade, cancel)

**Given** I am a sponsor
**When** I access my sponsor dashboard
**Then** I see all my sponsored animals, their status, and donation history

**Given** a sponsorship ends (cancellation or failed payment after retries)
**When** the sponsorship is marked inactive
**Then** the animal is no longer shown as sponsored by me

## Tasks

- T01: Design and implement animal sponsorship schema with tier levels
- T02: Integrate Stripe Billing API for recurring subscription management
- T03: Build sponsor dashboard and animal sponsorship page UI
- T04: Implement subscription lifecycle (create, pause, resume, cancel, upgrade/downgrade)
- T05: Add sponsorship data to animal profile and public-facing pages

## Definition of Done

- [ ] Sponsorship tiers created with correct pricing (Bronze $10, Silver $25, Gold $50)
- [ ] Stripe Subscriptions API integration working for recurring billing
- [ ] Sponsor dashboard displays all sponsored animals with tier and status
- [ ] Subscription management (pause, resume, cancel, change tier) works end-to-end
- [ ] Sponsorship information displayed on animal profile
- [ ] Confirmation emails sent on sponsorship creation and tier changes
- [ ] Unit tests cover sponsorship creation and status transitions (85%+ coverage)
- [ ] Integration tests cover full Stripe subscription lifecycle
- [ ] Failed payments handled gracefully with retry logic

## Technical Notes

- Sponsorship model: id, animal_id, donor_id, tier (enum: bronze, silver, gold), monthly_amount (decimal), subscription_start_date, subscription_end_date, stripe_subscription_id, status (active, paused, cancelled), created_date
- Tier pricing: Bronze 10 USD/month, Silver 25 USD/month, Gold 50 USD/month (configurable by region/currency)
- Stripe integration: create subscription on sponsorship creation, store subscription_id for management
- Subscription lifecycle: manage pause (invoices suspended) and resume (invoices resume) via Stripe
- Payment currency: support USD and EUR, convert PYG if needed
- Optional: tier perks (Gold gets monthly video update, Silver gets monthly photos, Bronze gets monthly status update)

## Dependencies

- Depends on: EPIC-10 (User authentication and donor accounts)
- Depends on: EPIC-3 (Payment processing and Stripe integration)
- Depends on: EPIC-1 (Animal catalog and records)
- Blocks: S02-sponsor-update-notifications (sponsor must exist before sending updates)

## Story Points: 8
