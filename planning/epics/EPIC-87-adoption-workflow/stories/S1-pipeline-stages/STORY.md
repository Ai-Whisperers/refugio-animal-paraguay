---
story: S1
epic: EPIC-87
ticket: RAP-588
title: "Configurable adoption pipeline stages"
status: ready
points: 5
priority: P0
track: Backend
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S1: Configurable adoption pipeline stages

## Story
As an **admin**, I want **to customize adoption stages** so that **workflow matches our organization's process**.

## Description
Create AdoptionStage model allowing organizations to customize adoption pipeline. Default stages provided but admins can add, remove, and reorder.

## Acceptance Criteria
- [ ] AdoptionStage model: id (UUID), organization_id (FK), name (string), order (int), is_required (bool), auto_advance (bool), timeout_days (int, nullable), created_at
- [ ] Default stages provided in migration: Application, Pre-qualification, Interview, Home Visit, Trial Period, Approval, Contract, Follow-up
- [ ] Each stage has: name, display order, whether it's required, auto-advance option, timeout (days before alert if stuck)
- [ ] GET /api/adoption-stages endpoint returns stages for organization, sorted by order
- [ ] POST /api/admin/adoption-stages creates new stage (auth: admin)
- [ ] PUT /api/admin/adoption-stages/{id} updates stage (name, order, is_required, etc)
- [ ] DELETE /api/admin/adoption-stages/{id} removes stage (soft delete)
- [ ] PATCH /api/admin/adoption-stages/reorder accepts list of stage IDs in new order, updates ordering
- [ ] Validation: stage names unique per organization, order field updated automatically
- [ ] Timeout alerts: if adoption stuck in stage for timeout_days, flag for staff review
- [ ] Auto-advance: if enabled, automatically move to next stage when conditions met (staff configurable)
- [ ] Migration creates default stages for existing organizations
- [ ] Unit tests: stage CRUD operations, ordering

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for CRUD operations
- [ ] Migration tested
- [ ] Deployed to staging and verified

## Technical Notes
- Use order integer field for stage ordering
- Implement soft delete with is_deleted flag
- Add indexes on organization_id, order
- Consider stage templates for common workflows

## Story Points: 5
