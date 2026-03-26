---
story: S04
epic: EPIC-12
title: Foster-to-Adopt Pathway
status: ready
created: 2026-03-26T00:00:00.000000
effort: 6
---

# S04: Foster-to-Adopt Pathway

## User Story

As a **foster family**, I want to **express my interest in adopting my foster animal and follow a fast-tracked adoption process** so that **I can keep an animal I've bonded with and the shelter gains a proven adopter**.

## Acceptance Criteria

**Given** I am a foster family with an active long-term placement (30+ days)
**When** I access my foster dashboard
**Then** I see a button to express adoption interest in my foster animal

**Given** I express adoption interest
**When** I submit an adoption interest form
**Then** my application is marked as "Foster Adoption" and skipped to staff approval step (no waiting period)

**Given** my foster adoption is approved
**When** I complete the adoption process
**Then** my adoption fees are waived or reduced (if configured by staff)

**Given** I am a foster family requesting adoption
**When** staff reviews my application
**Then** staff can see my complete fostering history, check-in record, and reliability metrics

**Given** foster adoptions are tracked
**When** I view the impact dashboard
**Then** foster-to-adoption conversion rate is displayed

## Tasks

- T01: Add adoption interest button and form to foster placement dashboard
- T02: Implement adoption application creation from foster interest (fast-track)
- T03: Build foster history context display for staff reviewing foster adoptions
- T04: Implement adoption fee waiver/reduction logic for foster adoptions
- T05: Add foster-to-adoption conversion metrics to impact reporting

## Definition of Done

- [ ] Foster families can express adoption interest with simple form
- [ ] Adoption application is created with fast-track flag set
- [ ] Staff review interface shows "Foster Adoption" designation and foster history
- [ ] Adoption fee waiver applies correctly based on configuration
- [ ] Foster-to-adoption conversion rate tracked and displayed in reports
- [ ] Unit tests cover fast-track logic and fee calculation (85%+ coverage)
- [ ] Integration tests cover full foster-to-adoption workflow
- [ ] No foster adoption applications allowed for placements < 30 days old

## Technical Notes

- Adoption interest model: placement_id, expressed_date, notes
- Fast-track flag in adoption_request: is_foster_adoption (boolean)
- Fee waiver: apply to adoption_fees table with reason = "foster_adoption"
- Conversion calculation: count adoptions where is_foster_adoption=true / count total foster placements ended (for a period)
- Show foster metrics on staff review: placement_duration, check_in_count, concern_count, avg_health_status
- Optional: require minimum check-in frequency or no flagged concerns before allowing foster adoption

## Dependencies

- Depends on: S02-foster-placement-matching (foster placement must exist)
- Depends on: EPIC-2 (Adoption process and workflows)
- Blocks: S05-foster-supply-cost-tracking (cost tracking may include foster adoption context)

## Story Points: 6
