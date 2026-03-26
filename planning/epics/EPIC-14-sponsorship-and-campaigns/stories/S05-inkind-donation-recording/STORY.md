---
story: S05
epic: EPIC-14
title: In-Kind Donation Recording
status: ready
created: 2026-03-26T00:00:00.000000
effort: 5
---

# S05: In-Kind Donation Recording

## User Story

As a **shelter staff member**, I want to **record non-cash donations (food, supplies, vet services) with estimated values** so that **we can quantify total donor contributions and include in-kind donations in impact reports**.

## Acceptance Criteria

**Given** I receive a donation of dog food, cat litter, or veterinary services
**When** I record the donation
**Then** I specify the item type, quantity, estimated value, and donor information

**Given** an in-kind donation is recorded
**When** I view donor records
**Then** I see both cash and in-kind contributions in their total giving history

**Given** I'm generating impact reports
**When** I include in-kind donations
**Then** the report shows total value (cash + in-kind) and breaks down by donation type

**Given** in-kind donations accumulate
**When** I export donation data
**Then** all donations (cash and in-kind) are included with their values

**Given** a specific supplier or vendor frequently donates items
**When** I record donations from them
**Then** I can track them as an organizational donor and see their total contributions

## Tasks

- T01: Extend donation schema to support in-kind donations with item type and estimated value
- T02: Build staff interface for recording in-kind donations
- T03: Implement donor total calculation (cash + in-kind value combined)
- T04: Add in-kind donations to impact reports and donor statements
- T05: Create in-kind donation analytics (by type, by donor, value trends)

## Definition of Done

- [ ] In-kind donation form captures: item_type, quantity, estimated_value, donor_name, date_received, notes
- [ ] Donor records show both cash and in-kind contributions
- [ ] Total donor giving = sum(cash_donations) + sum(in_kind_values)
- [ ] Impact reports include in-kind donation values
- [ ] In-kind donations can be filtered and aggregated by type
- [ ] Unit tests cover in-kind calculation and aggregation (80%+ coverage)
- [ ] Integration tests verify full in-kind donation recording and reporting
- [ ] No negative values in donation records due to adjustments

## Technical Notes

- In-kind donation model: id, donor_id, item_type (enum), quantity (int), estimated_value (decimal), currency (default: USD or org default), date_received, received_by_staff_id, notes, campaign_id (optional)
- Item type enum: food, medication, equipment, toys, bedding, supplies, veterinary_services, transportation, other
- Donation type determination: if amount_paid > 0 → cash_donation, else if estimated_value > 0 → in_kind_donation
- Total giving calculation: SUM(cash_donations.amount) + SUM(in_kind_donations.estimated_value) GROUP BY donor_id
- Analytics queries: COUNT and SUM by item_type, by date range, by donor
- Consider: predefined values for common items (case of dog food = $25, box of bandages = $15) for faster entry

## Dependencies

- Depends on: EPIC-3 (Donation system and donor records)
- Depends on: EPIC-13 (Impact reporting includes in-kind values)
- Blocks: None (terminal story)

## Story Points: 5
