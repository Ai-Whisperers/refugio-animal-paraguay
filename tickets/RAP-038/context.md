# RAP-038 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26 18:00

## Current Focus
Implementing campaign management feature: model design, Alembic migration, service layer, API endpoints, and comprehensive test coverage for fundraising campaign functionality.

## Technical State
- **Branch**: feature/RAP-038-campaign-management
- **Components in progress**:
  - Campaign model (src/db/models/campaign.py) — awaiting design
  - Campaign migration (src/db/migrations/versions/011_*.py) — not yet created
  - Campaign service (src/services/campaign_service.py) — awaiting model completion
  - Campaign API (src/api/campaigns.py) — awaiting service completion
  - Campaign schemas (src/schemas/campaign.py) — awaiting model completion
  - Tests (tests/unit/test_campaign*.py, tests/integration/test_campaign_api.py) — awaiting implementation

## Next Steps
1. Design Campaign model with status enum and relationships
2. Create Alembic migration 011 for campaign schema
3. Implement CampaignService with CRUD and progress calculation
4. Build campaign API endpoints with validation
5. Write unit and integration tests
6. Verify coverage and quality gates

## Blockers
None currently identified.

## Key Decisions Made
- Campaign status lifecycle: draft → active → completed (or cancelled)
- Progress calculation: current_total / goal_amount as decimal, percentage as integer
- Campaign-donation association: many-to-one (donations belong to campaigns), FK with ON DELETE RESTRICT
- Currency handling: campaigns have primary currency, donations converted before aggregation

## RESUME POINT
Ready to begin Phase 1 (data layer) — start with Campaign model design, focusing on:
- Status enum (draft, active, completed, cancelled)
- Required fields (title, description, goal_amount, currency, deadline, created_by, status)
- Timestamps (created_at, updated_at)
- Optional fields (image_url, target_animal_id for animal-specific campaigns)
- Relationships (creator FK, donations, target_animal FK if exists)
