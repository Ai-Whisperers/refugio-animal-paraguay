---
story: S10
epic: EPIC-80
ticket: RAP-542
title: "Integration with vet voucher system"
status: ready
points: 3
priority: P2
track: Backend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S10: Integration with vet voucher system

## Story
As a **rescuer**, I want **to claim vouchers from community donations** so that **I can access free veterinary services**.

## Description
Enable rescuers to claim vouchers from donations targeting their animals and location.

## Acceptance Criteria
- [ ] Voucher availability: rescuers can filter vouchers by: their location/area, service type they need
- [ ] GET /api/rescuer/vouchers/available endpoint: returns unclaimed vouchers available in rescuer's area, filtered by service type
- [ ] Claim flow: rescuer sees available vouchers, clicks "Use for [animal]", selects their animal from list, claims voucher
- [ ] Claimed voucher shows: in rescuer's voucher wallet, QR code, clinic details, "Ready to use" badge
- [ ] Rescuer profile: shows "X vouchers claimed" stat, "Voucher wallet" section in /portal/rescuer
- [ ] Usage tracking: rescuer can see vouchers used/pending redemption

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: vouchers available to rescuer in area
- [ ] Integration test: claim flow works
- [ ] Deployed to staging and verified

## Technical Notes
- Query: GET /api/rescuer/vouchers/available filtered by location and service type
- Location-based: haversine distance calculation (100km radius)
- Filtering: service_type in (castration_dog, castration_cat, consultation, etc.)
- Stat tracking: rescuer_id in VetVoucher where status='claimed'

## Story Points: 3
