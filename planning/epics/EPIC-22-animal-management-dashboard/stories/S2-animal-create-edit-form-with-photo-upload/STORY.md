---
story: S2
epic: EPIC-22
ticket: RAP-106
title: "Animal create/edit form with photo upload"
status: done
points: 8
priority: P0
track: Frontend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S2: Animal create/edit form with photo upload

## Story
As a **staff member**, I want **animal create/edit form with photo upload** so that **shelter operations are efficient and data-driven**.

## Description
Staff can add new animals and edit existing ones, including uploading photos.

## Acceptance Criteria

**Given** Given I click Add Animal
**When** When I fill in species, breed, name, age, gender, description
**Then** Then the animal is created and appears in the list

**Given** Given I am editing an animal
**When** When I upload a photo
**Then** Then the photo is saved and displayed as the animal's primary image

**Given** Given I edit an animal's details
**When** When I save changes
**Then** Then the changes are persisted and visible immediately

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-22
- Track: Frontend
- Priority: P0
- Sprint: 1

## Story Points: 8
