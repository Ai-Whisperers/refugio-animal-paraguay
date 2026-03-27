---
story: S3
epic: EPIC-26
ticket: RAP-127
title: "Diagnosis and treatment recording"
status: done
points: 5
priority: P0
track: Backend
sprint: 2
version: V5
created: 2026-03-26T19:06:04
---

# S3: Diagnosis and treatment recording

## Story
As a **system**, I want **diagnosis and treatment recording** so that **shelter operations are efficient and data-driven**.

## Description
API endpoints for recording diagnoses and treatments within vet visits.

## Acceptance Criteria

**Given** Given a vet visit exists
**When** When I POST a diagnosis with treatment plan
**Then** Then the diagnosis and treatment are linked to the visit

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-26
- Track: Backend
- Priority: P0
- Sprint: 2

## Story Points: 5
