# RAP-038 References

## Key Files

### Data Layer
- `src/db/models/campaign.py` — Campaign SQLAlchemy model (not yet created)
- `src/db/models/donation.py` — Donation model (existing, will add FK to campaign)
- `src/db/migrations/versions/011_*.py` — Alembic migration for campaign schema (not yet created)

### Service Layer
- `src/services/campaign_service.py` — CampaignService with CRUD and progress calculation (not yet created)

### API Layer
- `src/api/campaigns.py` — Campaign routes and endpoints (not yet created)
- `src/schemas/campaign.py` — Pydantic schemas for request/response (not yet created)

### Testing
- `tests/unit/test_campaign_model.py` — Campaign model and service tests (not yet created)
- `tests/integration/test_campaign_api.py` — Campaign API endpoint tests (not yet created)
- `tests/conftest.py` — Shared fixtures (existing, may extend)

## Related Stories
- **Parent Epic**: `planning/epics/EPIC-14-sponsorship-and-campaigns/EPIC.md`
- **User Story**: `planning/epics/EPIC-14-sponsorship-and-campaigns/stories/S03-fundraising-campaign-management/STORY.md`
- **Reference Stories**:
  - RAP-001 (Database schema setup)
  - RAP-003 (API scaffold and patterns)
  - RAP-005 (Donation model and API)

## Design References
- Campaign status transitions: draft → active → completed | cancelled
- Currency handling: campaigns have base currency, donations converted for aggregation
- Progress tracking: current_total (sum of donations in campaign currency), goal_amount, percentage_toward_goal
- Relationships: Campaign (1) ← (many) Donations, Campaign (1) ← (many) DonationEvents

## Database Schema Notes
- Campaign table: id, title, description, goal_amount, currency, status, deadline, created_by (FK to users), created_at, updated_at
- Donation table: add campaign_id (FK) with ON DELETE RESTRICT
- Indexes: campaign.status, campaign.deadline, donation.campaign_id
