---
id: EPIC-14
title: Sponsorship & Campaigns
description: Animal sponsorship program, fundraising campaigns with goals, and in-kind donation tracking
status: planning
priority: high
estimated_effort: 50 story points
stories_count: 5
target_version: V2-V3
---

# EPIC-14: Sponsorship & Campaigns

## Overview

Build the emotional connection layer between donors and animals. Animal sponsorship ("I'm supporting Rocky's care") drives 3x higher donor retention than generic donations. Fundraising campaigns with goals and progress bars create urgency. In-kind donation tracking captures the full support picture for EU funder reports.

## Why This Epic Matters

- **Revenue driver**: Sponsorship programs generate recurring revenue with minimal acquisition cost
- **Donor retention**: Tangible impact stories ("Your EUR 25 paid for Rocky's vaccination") drive repeat giving
- **EU funder appeal**: Campaigns demonstrate organizational capacity and community support
- **Complete picture**: In-kind donations (volunteer time, donated supplies, pro-bono vet care) often exceed cash — EU funders value this
- **Social proof**: Campaign progress bars and success stories drive new donor acquisition

## Scope

### In Scope
- Animal sponsorship tiers with monthly/annual options
- Sponsor-to-animal matching and lifecycle tracking
- Sponsor update notifications (photos, milestones)
- Fundraising campaign creation with goals, deadlines, progress
- In-kind donation recording and valuation
- Campaign analytics and ROI tracking

### Out of Scope
- Peer-to-peer fundraising (donors create their own campaigns — V6+)
- Corporate sponsorship management (manual for now)
- Gift matching automation (manual tracking)
- Merchandise/shop integration (future)

## Stories

- [ ] S01: Animal Sponsorship Tiers & Matching
- [ ] S02: Sponsor Update Notifications
- [ ] S03: Fundraising Campaign Management
- [ ] S04: Campaign Progress & Social Proof
- [ ] S05: In-Kind Donation Recording

## Version Allocation

| Story | Version | Rationale |
|-------|---------|-----------|
| S01: Sponsorship Tiers | V2 | Launch alongside donation infrastructure |
| S02: Sponsor Updates | V3 | Needs notification engine from V3 |
| S03: Campaign Management | V2 | Emergency fund campaigns needed early |
| S04: Campaign Progress | V3 | Public-facing, needs frontend polish |
| S05: In-Kind Recording | V2 | Simple form, high value for funder reporting |

## Dependencies

- **Requires**: EPIC-3 (payment processing for sponsorships), EPIC-1 (animal data), EPIC-6 (sponsor notifications)
- **Consumed by**: EPIC-7 (dashboard shows campaign metrics), EPIC-13 (impact reports include sponsorship data)

## Technical Considerations

### Sponsorship Model

```
SponsorshipTier
  - id, name (Bronze/Silver/Gold or custom)
  - amount_eur, amount_pyg, frequency (monthly/annual/one_time)
  - benefits (JSONB: includes_updates, includes_certificate, includes_visit)
  - active, created_at

Sponsorship
  - id, sponsor_id (FK → Donor), animal_id (FK), tier_id (FK)
  - started_at, ended_at, status (active/paused/cancelled/completed)
  - stripe_subscription_id (for recurring)
  - total_contributed_eur

SponsorUpdate
  - id, sponsorship_id (FK), created_by (FK → User)
  - title, message, photos (ARRAY)
  - sent_at, delivery_status

Campaign
  - id, title, description, goal_amount_eur
  - raised_amount_eur, donor_count
  - start_date, end_date, status (draft/active/completed/cancelled)
  - category (emergency/medical/general/facility)
  - created_by (FK), featured (boolean)

InKindDonation
  - id, donor_id (FK, nullable), donor_name (for unregistered donors)
  - item_type (food/supplies/services/equipment)
  - description, quantity, estimated_value_eur
  - received_at, recorded_by (FK)
```

### Sponsorship-to-Stripe Mapping

- Monthly sponsorship → Stripe Subscription with `price` per tier
- Annual sponsorship → Stripe Subscription (yearly interval)
- One-time sponsorship → Regular PaymentIntent tagged with `animal_id`
- Cancelled sponsorship → Stripe subscription cancellation + status update
- Sponsor animal adopted → Notification + option to sponsor another animal

### Campaign Progress Real-time

- Option A: WebSocket push on new donation (V3+)
- Option B: 30-second polling from frontend (V2, simpler)
- Campaign completion triggers: auto-close donations, send thank-you to all donors

## Risks

| Risk | Mitigation |
|------|------------|
| Sponsored animal dies | Sensitive notification, offer to redirect sponsorship |
| Sponsored animal adopted | Celebration notification, offer new animal |
| Campaign doesn't reach goal | No penalty — show progress, extend deadline option |
| In-kind valuation disputes | Staff estimates with standard rates, flag as "estimated" |
| Sponsor expects exclusive access | Clear terms: sponsorship supports care, doesn't grant ownership |
