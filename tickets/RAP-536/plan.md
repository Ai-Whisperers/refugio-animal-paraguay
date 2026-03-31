# RAP-536 Plan

## Objective
Allow rescuers to create and manage fundraising campaigns for specific rescue efforts.

## Description
Rescuers need to create campaigns tied to their profile, with a target amount (EUR), animal involvement,
photos, and a goal message. Verified rescuers get auto-approval; unverified require admin approval.
Donors can find and donate to rescuer campaigns via public pages. Rescuers can end campaigns
to trigger impact notifications.

## Acceptance Criteria
- [ ] GET /api/portal/rescuer/campaigns — lists authenticated rescuer's campaigns
- [ ] POST /api/portal/rescuer/campaigns — creates a campaign (title, description, target_amount, animals, photos, goal_message)
- [ ] Auto-approval for verified rescuers, pending for unverified
- [ ] PATCH /api/portal/rescuer/campaigns/{id}/status — end/archive campaign
- [ ] Public route GET /api/rescuers/{slug}/campaigns/{campaign_id} — campaign detail with progress, donor count
- [ ] Frontend: /portal/rescuer/campaigns page with list + create button + modal form
- [ ] Frontend: /rescuers/{slug}/campaigns/{campaign_id} public detail page
- [ ] Unit tests for campaign creation logic (auto-approval, status)
- [ ] Integration test: create campaign endpoint returns 201

## Complexity Assessment
**Track**: Complex Implementation
**Assessment**: Fullstack (backend model/API + frontend pages) but well-bounded by existing campaign + rescuer patterns.

## Approach
1. Add rescuer_id FK to campaigns table via migration (nullable)
2. Create portal API router: src/api/rescuer_campaigns.py
3. Register router in app.py
4. Frontend: portal/rescuer/campaigns/page.tsx (list + create modal)
5. Frontend: rescuers/[slug]/campaigns/[id]/page.tsx (public detail)
6. Unit tests + integration tests

## Dependencies
- RAP-534 (Rescuer profile page) — DONE
- Campaign model and existing campaign API — existing

## Risks
- Migration: adding rescuer_id to campaigns table — low risk (nullable FK)
