---
story: S02
epic: EPIC-12
title: Foster Placement Matching
status: ready
created: 2026-03-26T00:00:00.000000
effort: 8
---

# S02: Foster Placement Matching

## User Story

As a **shelter staff member**, I want to **match animals with appropriate foster families based on compatibility factors** so that **animals get proper care in home environments and foster families have a good experience**.

## Acceptance Criteria

**Given** I am a staff member with animals needing foster homes
**When** I access the foster placement interface
**Then** the system shows available foster families filtered by species preference and current capacity

**Given** I select a specific animal and foster family
**When** I create a placement
**Then** the system records the placement date, expected return date, and current status

**Given** an animal is placed with a foster family
**When** the placement is active
**Then** the animal's status is updated to "In Foster Care" and the foster family's available capacity decreases

**Given** a placement is created
**When** email notification is sent to the foster family
**Then** it includes animal details, care instructions, and emergency contact information

**Given** I need to unplace an animal early
**When** I mark the placement as ended
**Then** the system updates the animal status and restores capacity to the foster family

## Tasks

- T01: Implement compatibility matching algorithm (species, capacity, experience)
- T02: Build staff placement interface with foster family selection
- T03: Create placement record schema and database persistence
- T04: Implement animal status transitions (available → in foster care → ready for adoption)
- T05: Add capacity calculation and enforcement logic

## Definition of Done

- [ ] Matching algorithm correctly filters foster families by species and capacity
- [ ] Placement interface allows staff to select animal and foster family
- [ ] Placement status transitions work correctly (active → ended)
- [ ] Animal and foster family records update appropriately on placement change
- [ ] Placement notification emails include all required information
- [ ] Unit tests cover matching logic and capacity calculations (85%+ coverage)
- [ ] Integration tests cover full placement workflow
- [ ] No race conditions when multiple staff members create placements simultaneously

## Technical Notes

- Matching algorithm: species match (required) + capacity available (required) + minimum experience level (optional filter)
- Placement record fields: id, animal_id, foster_family_id, start_date, expected_return_date, actual_return_date, status, notes
- Status enum: active, ended, on_hold
- Capacity calculation: track current placements count vs. family max capacity
- Use transaction isolation to prevent overbooking

## Dependencies

- Depends on: S01-foster-family-registration (approved foster families must exist)
- Depends on: EPIC-1 (Animal records and status management)
- Blocks: S03-foster-checkin-monitoring (placement must exist before check-ins)

## Story Points: 8
