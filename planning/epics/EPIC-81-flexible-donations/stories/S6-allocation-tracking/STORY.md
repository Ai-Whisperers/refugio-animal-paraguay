---
story: S6
epic: EPIC-81
ticket: RAP-548
title: "Donation allocation tracking API"
status: ready
points: 5
priority: P1
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S6: Donation allocation tracking API

## Story
As a **system**, I want **to track how donations are allocated** so that **donors know their impact**.

## Description
Create donation allocation tracking to link donations to specific expenses/uses.

## Acceptance Criteria
- [ ] DonationAllocation model: donation_id (FK), expense_id (FK), amount_allocated (in cents), allocated_at, note
- [ ] Admin can allocate donations: /admin/donations/{id}/allocate endpoint, select expense(s), allocate amount
- [ ] Expense model: for tracking costs (food purchase, vet bill, transport, etc.), id, description, category (food|medical|transport|housing|other), amount_cents, expense_date, related_animal_id (optional)
- [ ] GET /api/donations/{id}/allocation: returns how donation was allocated across expenses
- [ ] Dashboard: /admin/donation-allocations shows all allocations, pending allocations, allocation rate (%)
- [ ] Allocation rate: (allocated_amount / total_donations) * 100
- [ ] Unallocated: donations not yet allocated tracked separately
- [ ] Impact report: donor can request to see how their donations were used

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test allocation, rate calculation
- [ ] Integration test: allocate donation to expense
- [ ] Integration test: get allocation details
- [ ] Integration test: unallocated count correct
- [ ] Deployed to staging and verified

## Technical Notes
- DonationAllocation: many-to-one with Donation (one donation split across multiple expenses)
- Allocation endpoint: admin auth required
- Admin dashboard: query allocations with GROUP BY, calculate rates
- Reporting: aggregate allocations by category for impact reporting

## Story Points: 5
