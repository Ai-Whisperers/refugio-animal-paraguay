# RAP-072 Plan

## Objective
Complete the Fundraising Campaign Management feature by adding `featured` flag, `paused`/`archived` status values, `photo_urls` array, and `days_remaining` to campaign APIs.

## Description
The campaign foundation (CRUD, progress tracking, public listing) was partially implemented in prior work. This ticket closes the remaining gaps against EPIC-14 S03 acceptance criteria: featured campaigns on the public page, paused/archived lifecycle states, multi-photo support, and days-remaining display.

## Acceptance Criteria
- [ ] Campaign model has `featured` boolean field (default false)
- [ ] Campaign status enum supports: draft, active, paused, completed, archived
- [ ] Campaign model has `photo_urls` text array for multiple photos
- [ ] Staff can filter admin campaign list by `featured=true/false`
- [ ] Staff can set `featured=true` to promote a campaign
- [ ] Public listing accepts `?featured=true` to surface featured campaigns
- [ ] Public campaign response includes `days_remaining` (null if no deadline)
- [ ] Migration 016 applies cleanly to existing schema
- [ ] Unit tests: status lifecycle + featured flag + days_remaining (≥85% coverage for new code)
- [ ] Integration tests: full lifecycle (draft→active→paused→completed), featured filter

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria
- [ ] Single, clear root cause identified — multiple gaps
- [ ] Solution affects ≤3 files — affects 6+ files
- [ ] Change impact ≤10 lines — ~150 lines
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Complex — multiple model/schema/API/test changes, new migration required

## Approach
1. New Alembic migration 016: ADD COLUMN featured BOOL, ALTER CHECK for new statuses, ADD COLUMN photo_urls TEXT[]
2. Update Campaign ORM model
3. Update CampaignCreate/CampaignUpdate/CampaignResponse/CampaignPublicResponse schemas
4. Update admin_campaigns.py: add `featured` query param to list endpoint
5. Update public_campaigns.py: add `featured` filter, compute `days_remaining`
6. Add unit tests for new fields + status transitions
7. Add integration tests for featured filter and lifecycle

## Dependencies
- Depends on: Migration 013 (campaigns table exists)
- Depends on: RAP-009 (donation model for progress tracking)
- Blocks: S04-campaign-progress-social-proof

## Risks
- Risk: Migration CHECK constraint update may fail if existing data has old statuses → Mitigation: check constraint is additive (add paused/archived, keep cancelled for backward compat)
