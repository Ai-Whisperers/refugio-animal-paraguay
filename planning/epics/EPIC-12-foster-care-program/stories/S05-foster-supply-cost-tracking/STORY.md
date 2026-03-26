---
story: S05
epic: EPIC-12
title: Foster Supply & Cost Tracking
status: ready
created: 2026-03-26T00:00:00.000000
effort: 5
---

# S05: Foster Supply & Cost Tracking

## User Story

As a **shelter staff member**, I want to **track supplies provided to foster homes (food, medication, equipment) with estimated costs** so that **I can report on the true cost of foster care and demonstrate the value fostering provides to donors and funders**.

## Acceptance Criteria

**Given** I am a staff member managing foster placements
**When** I record a supply distribution to a foster family
**Then** I specify the supply type, quantity, and estimated cost

**Given** a supply has been recorded for a foster placement
**When** I view the placement detail
**Then** I see the total cost of supplies provided and a list of each supply

**Given** multiple placements are active
**When** I generate a cost report
**Then** the report aggregates supply costs by placement, by foster family, and by supply type

**Given** a foster placement ends
**When** I record the final return of supplies
**Then** remaining supplies are tracked and their costs are deducted from total foster cost

**Given** I'm reporting foster program impact to donors
**When** I export the foster program data
**Then** cost breakdown is included: medical vs. food vs. equipment vs. other

## Tasks

- T01: Design and implement foster supply record schema and API
- T02: Build staff interface for recording supply distributions
- T03: Create cost calculation and aggregation logic
- T04: Implement supply tracking with return/deduction workflow
- T05: Add foster supply costs to impact reporting and export functionality

## Definition of Done

- [ ] Supply distribution form captures type, quantity, estimated cost, and date
- [ ] Placement detail view shows total supplies cost and itemized list
- [ ] Cost aggregation reports available by placement, family, and supply type
- [ ] Supply return workflow deducts costs correctly
- [ ] Export includes cost breakdown in foster program data
- [ ] Unit tests cover cost calculations and aggregations (85%+ coverage)
- [ ] Integration tests cover full supply lifecycle (add → report → return)
- [ ] No negative costs due to multiple return transactions

## Technical Notes

- Foster supply model: id, placement_id, supply_type (enum), quantity (int), estimated_cost (decimal), recorded_date, recorded_by_staff_id, notes
- Supply type enum: food, medication, equipment, toys, bedding, other
- Cost aggregation: SUM(estimated_cost) GROUP BY placement_id, foster_family_id, supply_type
- Return transaction: negative record with same supply type and quantity
- Export format: CSV or PDF with cost breakdown summary
- Consider: setting up predefined supply costs for common items to speed data entry

## Dependencies

- Depends on: S02-foster-placement-matching (supply tracking tied to placements)
- Depends on: EPIC-13 (Impact reporting and compliance)
- Blocks: EPIC-13.S04-fund-allocation-tracking (foster costs feed into fund allocation breakdown)

## Story Points: 5
