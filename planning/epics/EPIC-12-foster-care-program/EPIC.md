---
id: EPIC-12
title: Foster Care Program
description: Enable foster family registration, animal placement, check-in monitoring, and foster-to-adopt pathway
status: planning
priority: medium
estimated_effort: 55 story points
stories_count: 5
target_version: V4
---

# EPIC-12: Foster Care Program

## Overview

Build a complete foster care management system allowing the shelter to extend its capacity beyond physical walls. Foster families register, receive animal placements, submit regular check-ins, and can fast-track to adoption. This program is critical for Paraguay's context where shelter capacity is limited and fosters provide socialization that improves adoptability.

## Why This Epic Matters

- **Capacity multiplier**: Every foster home is an extra shelter bed without construction costs
- **Better outcomes**: Animals in foster homes socialize faster and are more adoptable
- **EU funder appeal**: Foster programs demonstrate community engagement and cost efficiency
- **Adoption pipeline**: 40-60% of fosters become adopters (industry average) — pre-vetted, high success rate

## Scope

### In Scope
- Foster family registration with home assessment data
- Animal-to-foster matching based on capacity and compatibility
- Placement lifecycle (place, monitor, return, extend)
- Regular check-in submissions with photos
- Foster-to-adopt conversion pathway
- Foster supply tracking and cost analysis

### Out of Scope
- Video consultations with foster families (future)
- Automated foster matching algorithm (V5+ enhancement)
- Foster family background check integration (manual process)
- Multi-shelter foster network (future)

## Stories

- [ ] S01: Foster Family Registration & Profiles
- [ ] S02: Foster Placement & Matching
- [ ] S03: Foster Check-in & Monitoring
- [ ] S04: Foster-to-Adopt Pathway
- [ ] S05: Foster Supply & Cost Tracking

## Dependencies

- **Requires**: EPIC-1 (animal records), EPIC-10 (user accounts for foster role), EPIC-6 (check-in reminders)
- **Blocks**: EPIC-7 (dashboard needs foster metrics), EPIC-13 (impact reporting includes foster outcomes)

## Technical Considerations

### New Database Models

```
FosterFamily
  - id, user_id (FK), home_type (house/apartment/farm), yard_size
  - experience_level (none/some/experienced), max_animals, species_preference
  - has_children, has_other_pets, emergency_contact
  - status (pending_review/active/inactive/suspended)
  - created_at, updated_at

FosterPlacement
  - id, animal_id (FK), foster_family_id (FK), placed_by (FK → User)
  - placed_at, expected_return_at, actual_return_at
  - status (active/completed/extended/emergency_return)
  - notes, return_reason

FosterCheckIn
  - id, placement_id (FK), submitted_by (FK)
  - health_status (excellent/good/concerning/emergency)
  - appetite, energy_level, behavior_notes
  - photos (ARRAY), submitted_at

FosterSupply
  - id, placement_id (FK), item_type (food/medication/equipment)
  - description, quantity, estimated_value_pyg
  - provided_at
```

### New API Routers

- `src/api/foster.py` — Foster family CRUD, placement management, check-in submissions

### New Roles

- **foster**: Can view placed animal profile, submit check-ins, update own profile

## Risks

| Risk | Mitigation |
|------|------------|
| Foster families don't submit check-ins | WhatsApp reminders + simple form (3 taps + photo) |
| Emergency returns without notice | Emergency protocol with staff notification chain |
| Foster home not suitable | Pre-placement review checklist, trial period |
| Supply costs exceed budget | Track costs per placement, set supply limits |
