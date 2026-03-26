---
story: S04
epic: EPIC-14
title: Campaign Progress & Social Proof
status: ready
created: 2026-03-26T00:00:00.000000
effort: 5
---

# S04: Campaign Progress & Social Proof

## User Story

As a **potential donor**, I want to **see campaign progress bars, recent donor names, and donation counts** so that **social proof and momentum motivate me to donate**.

## Acceptance Criteria

**Given** I am viewing a fundraising campaign
**When** I look at the campaign page
**Then** I see a visual progress bar showing amount raised vs. goal

**Given** a campaign has received donations
**When** I scroll through the campaign
**Then** I see recent donor names (first names only if privacy-enabled) and their donation amounts

**Given** multiple donors have contributed
**When** I view the campaign
**Then** I see "X donors have already contributed $Y to this campaign"

**Given** a campaign is gaining momentum
**When** I view the campaign
**Then** I see recent donations listed (last 10) with timestamps to show active support

**Given** I'm considering a donation
**When** I see social proof (donor count, amount raised)
**Then** it influences my decision to donate

## Tasks

- T01: Design campaign progress visualization component
- T02: Implement recent donor display with privacy controls
- T03: Create donation count and momentum metrics on campaign detail page
- T04: Build donation leaderboard (optional: top 10 donors for campaign)
- T05: Add analytics tracking for social proof engagement

## Definition of Done

- [ ] Progress bar displays correctly: (amount_raised / goal) * 100%
- [ ] Recent donors listed with first name, amount, and relative timestamp (e.g., "2 hours ago")
- [ ] Donors can opt out of public listing via privacy preference
- [ ] Donor count and total raised prominently displayed
- [ ] Social proof elements render correctly on mobile and desktop
- [ ] Unit tests cover calculation logic (80%+ coverage)
- [ ] Integration tests verify donor privacy preferences respected
- [ ] Performance: campaign detail page loads in < 2 seconds

## Technical Notes

- Progress bar data: current_total, goal_amount, percentage = (current_total / goal_amount) * 100
- Recent donors display: query last 10 donations for campaign where donor.show_in_public=true, order by donation_date DESC
- Donor display fields: first_name (or "Anonymous" if opted out), amount, donation_date
- Privacy model: donor.show_in_public (bool), extends existing user privacy settings
- Momentum metric: donations_in_last_7_days, donations_in_last_24_hours
- Optional: gamification - milestone rewards (hit $5k, celebrate on campaign page)
- Analytics: track clicks on "Donate" button before/after seeing social proof

## Dependencies

- Depends on: S03-fundraising-campaign-management (campaigns must exist)
- Depends on: EPIC-3 (Donation data available)
- Blocks: None (terminal story)

## Story Points: 5
