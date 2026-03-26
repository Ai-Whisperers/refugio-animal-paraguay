# RAP-041 Plan

## Objective
Implement the Donation Landing Page with campaign-based fundraising, including backend campaign model/API and frontend campaign browsing + donation form.

## Description
The shelter needs a public-facing donation experience that shows fundraising campaigns with progress tracking, allows donors to contribute via Stripe (EUR/USD) or bank transfer (PYG), and gives staff the ability to manage campaigns. This replaces the current static donate page with a dynamic, campaign-driven experience.

## Acceptance Criteria
- [ ] Campaign model exists in database with migration applied
- [ ] Public endpoints: GET /public/campaigns (list), GET /public/campaigns/{id} (detail with progress)
- [ ] Admin endpoints: POST /admin/campaigns (create), PATCH /admin/campaigns/{id} (update)
- [ ] Donations can be linked to a campaign (campaign_id FK)
- [ ] Frontend donate page shows active campaigns with progress bars
- [ ] Frontend campaign detail page with donation form
- [ ] Donation form supports amount entry and payment method selection
- [ ] Unit tests for campaign schemas and validation
- [ ] Integration tests for campaign endpoints
- [ ] All quality gates pass (ruff, black, pytest)

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified — N/A (new feature)
- [x] Solution affects ≤3 files — NO, affects 10+ files
- [ ] Change impact ≤10 lines of actual code — NO
- [ ] Low risk of side effects — Moderate (new migration, FK changes)
- [ ] Solution pattern is well-understood — YES

**Assessment result**: Complex — new model, migration, multiple endpoints, frontend pages

## Approach
1. Create Campaign ORM model and Alembic migration
2. Create Pydantic schemas for campaigns
3. Implement public campaign endpoints (list + detail)
4. Implement admin campaign endpoints (create + update)
5. Add campaign_id to donation creation flow
6. Build frontend campaign list and detail pages
7. Build donation form component
8. Write unit + integration tests

## Dependencies
- Depends on: RAP-009 (Stripe foundation) — DONE
- Depends on: existing donation model — DONE

## Risks
- Risk: Migration conflicts with other branches → Mitigation: Use next available migration number
- Risk: Stripe integration complexity → Mitigation: Reuse existing PaymentIntent flow
