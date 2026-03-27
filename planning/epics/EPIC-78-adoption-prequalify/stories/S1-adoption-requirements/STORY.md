---
story: S1
epic: EPIC-78
ticket: RAP-517
title: "Configurable adoption requirements model"
status: ready
points: 5
priority: P0
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S1: Configurable adoption requirements model

## Story
As an **adoption administrator**, I want **to define custom adoption requirements per animal** so that **I can filter unsuitable adopters early**.

## Description
Create AdoptionRequirement model allowing admin to configure requirements globally or per-animal. Requirements specify conditions adopters must meet.

## Acceptance Criteria
- [ ] AdoptionRequirement model/table with columns: id (UUID PK), animal_id (FK, nullable for global requirements), requirement_type (enum: yard_required|no_children_under|experience_required|home_type|max_hours_alone|other_pets_ok|housing_status|income_requirement), value (JSON, stores different data per type), is_mandatory (bool, default true), active (bool, default true), created_at, updated_at
- [ ] Requirement types and value format:
  - yard_required: value = {"yard": "required"|"preferred"|"not_needed"}
  - no_children_under: value = {"age": N (int, e.g. 5 means no children under 5)}
  - experience_required: value = {"level": "none"|"some"|"experienced"}
  - home_type: value = {"types": ["apartment", "house", "farm"] (array of allowed types)}
  - max_hours_alone: value = {"hours": N (int, max hours alone per day)}
  - other_pets_ok: value = {"pets": ["cats", "dogs", "other"] (array of compatible pets)}
  - housing_status: value = {"status": "owned"|"rented"}
  - income_requirement: value = {"monthly": N (in EUR cents)}
- [ ] POST /admin/adoption-requirements endpoint: creates global requirement, requires admin auth
- [ ] POST /admin/animals/{animal_id}/requirements endpoint: creates animal-specific requirement, overrides global, requires admin auth
- [ ] GET /admin/animals/{animal_id}/requirements endpoint: list all requirements for animal (global + specific), merged into single list
- [ ] PUT /admin/animals/{animal_id}/requirements/{req_id} endpoint: update requirement, requires admin auth
- [ ] DELETE /admin/animals/{animal_id}/requirements/{req_id} endpoint: soft-delete requirement (set active=false)
- [ ] GET /api/animals/{animal_id}/pre-qualify endpoint: returns list of questions to ask adopter based on animal's requirements
- [ ] Global defaults: platform admin can set global requirements that apply to all animals unless overridden per-animal
- [ ] Mandatory vs preferred: mandatory requirements disqualify if not met, preferred requirements reduce match score but don't disqualify
- [ ] Response format: {id, requirement_type, value, is_mandatory, animal_id (if specific), human_readable_description}

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test requirement creation, value validation, inheritance (global vs specific)
- [ ] Integration test: create global requirement and animal-specific requirement, merge correctly
- [ ] Integration test: update requirement and verify changes
- [ ] Integration test: soft delete requirement
- [ ] Integration test: override global with animal-specific requirement
- [ ] Database migration created
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoints in admin module
- Database: AdoptionRequirement table with JSON column for value (PostgreSQL JSONB recommended)
- Validation: validate value JSON against schema for each requirement_type
- Merging: query global requirements + animal-specific requirements, animal-specific overrides global of same type
- Human-readable descriptions: map requirement_type to user-friendly text for UI
- Global requirements: stored with animal_id=NULL, fetched separately
- Soft delete: set active=false, never actually delete

## Story Points: 5
