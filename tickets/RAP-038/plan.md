# RAP-038 Plan

## Objective
Implement campaign management feature to enable fundraising campaigns with goals, deadlines, and real-time donation tracking.

## Description
The platform needs to support structured fundraising campaigns tied to specific causes or animals. Each campaign must track progress toward monetary goals, enforce deadline constraints, and associate donations with their parent campaign. This enables the shelter to run targeted fundraising initiatives and provide transparency to donors about campaign performance.

## Acceptance Criteria
- [ ] Campaign model created with status lifecycle (draft, active, completed, cancelled)
- [ ] Alembic migration 011 applied for campaign schema
- [ ] CRUD API endpoints: POST /campaigns, GET /campaigns/{id}, PATCH /campaigns/{id}, DELETE /campaigns/{id}, GET /campaigns (list)
- [ ] Campaign-donation association implemented (foreign key, cascade rules)
- [ ] Campaign progress calculation (current_total, percentage_toward_goal)
- [ ] Unit tests for Campaign model and service methods (≥90% coverage)
- [ ] Integration tests for campaign API endpoints and donation association (happy path + edge cases)
- [ ] All tests passing, coverage at or above 80%

## Complexity Assessment
**Track**: Complex Implementation

### Complex Indicators (met)
- [ ] Multiple interdependent components (model, migration, service, API)
- [ ] Changes affect >3 files
- [ ] New database relationship (campaign ↔ donation)
- [ ] Status lifecycle and validation logic
- [ ] Phased approach required

**Assessment result**: Complex — requires model design, migration, service layer, API integration, and comprehensive testing. Multiple phases needed.

## Approach

### Phase 1: Data Layer
1. Design Campaign model (SQLAlchemy)
2. Create Alembic migration 011
3. Update Donation model with campaign_id FK

### Phase 2: Service Layer
1. Implement CampaignService with CRUD methods
2. Add progress calculation logic
3. Handle campaign-donation associations

### Phase 3: API Layer
1. Define CampaignCreate, CampaignUpdate, CampaignResponse schemas
2. Implement campaign routes with auth/validation
3. Add campaign filtering to donation endpoints

### Phase 4: Testing & Validation
1. Unit tests for model, service, validation
2. Integration tests for API endpoints
3. Coverage verification
4. Quality gates

## Dependencies
- Depends on: RAP-001 (database setup), RAP-003 (API scaffold)
- Blocks: EPIC-14 downstream features (campaign performance reporting, sponsor management)

## Risks
- **Risk**: Campaign-donation association requires careful FK constraint design → **Mitigation**: Use ON DELETE RESTRICT to prevent accidental campaign deletion with active donations
- **Risk**: Progress calculation complexity for campaigns with multiple currency donations (EUR/PYG) → **Mitigation**: Store goal in campaign default currency, convert donations to campaign currency before calculation
- **Risk**: Race conditions on campaign status updates during concurrent donation submissions → **Mitigation**: Use database transaction isolation, test with concurrent load
