---
story: S03
epic: EPIC-14
title: Fundraising Campaign Management
status: done
created: 2026-03-26T00:00:00.000000
effort: 6
---

# S03: Fundraising Campaign Management

## User Story

As a **shelter staff member**, I want to **create and manage fundraising campaigns with goals, deadlines, and descriptions** so that **we can run multiple campaigns simultaneously and track progress toward specific funding objectives**.

## Acceptance Criteria

**Given** I am a staff member with campaign permissions
**When** I create a new fundraising campaign
**Then** I specify title, description, goal amount (USD/EUR), deadline, and category

**Given** a campaign is created
**When** I view the campaign
**Then** I can edit all details, add/remove photos, and update status (active, paused, completed, archived)

**Given** a campaign is active
**When** donors make donations to that campaign
**Then** the donation is recorded as belonging to the campaign and counts toward the goal

**Given** a campaign is approaching its deadline
**When** I view campaign details
**Then** I see the days remaining and current progress (X of Y goal)

**Given** I want to feature certain campaigns
**When** I set a campaign to "featured"
**Then** it appears prominently on the public fundraising page

## Tasks

- T01: Design and implement campaign schema with status lifecycle
- T02: Build staff campaign management interface (CRUD operations)
- T03: Implement campaign-donation association and progress tracking
- T04: Create public campaign listing and detail pages
- T05: Add campaign data to impact reporting and analytics

## Definition of Done

- [ ] Campaign creation form validates required fields (title, goal, deadline)
- [ ] Staff can update all campaign fields and status
- [ ] Donations correctly associated with campaigns
- [ ] Campaign progress calculated as: sum(donations) / goal_amount
- [ ] Public campaign pages show clear progress and deadline info
- [ ] Featured campaigns displayed on homepage/fundraising page
- [ ] Unit tests cover campaign status transitions and progress calculation (85%+ coverage)
- [ ] Integration tests verify full campaign lifecycle (create → active → completed)
- [ ] Campaign totals match donation sum exactly (no rounding errors)

## Technical Notes

- Campaign model: id, title (text), description (text), goal_amount (decimal), currency (enum: USD, EUR), category (enum: medical, food, operations, rescue, facility, other), deadline_date (date), created_date, created_by_staff_id, status (enum: draft, active, paused, completed, archived), featured (bool), photo_urls (array)
- Category enum: medical, food, operations, rescue, facility, other (maps to fund allocation categories)
- Progress calculation: SUM(donations.amount) WHERE donations.campaign_id = campaign.id
- Featured campaigns: limited to 3-5 displayed on homepage
- Status lifecycle: draft → active → paused (optional) → completed/archived
- Consider: auto-complete campaigns when deadline passed and goal reached

## Dependencies

- Depends on: EPIC-3 (Donation recording and tracking)
- Depends on: EPIC-11 (Public portal for campaign display)
- Blocks: S04-campaign-progress-social-proof (public page uses campaign data)

## Story Points: 6
