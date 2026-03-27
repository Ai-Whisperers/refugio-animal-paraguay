---
story: S6
epic: EPIC-84
ticket: RAP-571
title: "Referral tracking"
status: ready
points: 5
priority: P2
track: Backend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S6: Referral tracking

## Story
As an **admin**, I want **to identify sharers who drive donations and adoptions** so that **I can recognize and reward top advocates**.

## Description
Enhance share tracking with referral attribution. Track which user's share led to a donation or adoption application. Provide referrer leaderboards and conversion metrics.

## Acceptance Criteria
- [ ] Share URLs include ?ref=USER_ID parameter for attribution (auto-generated in share links)
- [ ] URL format: https://refugio.app/animals/abc123?ref=user_id_xyz
- [ ] On landing, store ref=USER_ID in session/localStorage
- [ ] When user donates or applies for adoption: include referrer_user_id from session
- [ ] Donation model extended: referrer_user_id (FK to User, nullable)
- [ ] AdoptionRequest model extended: referrer_user_id (FK to User, nullable)
- [ ] GET /admin/referrals endpoint returns referral metrics: total referrers, donations by referrer, adoption applications by referrer
- [ ] GET /admin/referrals/leaderboard returns top 10 referrers by donation amount and count
- [ ] Metrics include: total donations attributed, total adoption applications attributed, conversion rate
- [ ] Referrer conversion rate: count of referrals that became donors/adopters / count of total referrals
- [ ] Optional: Referrer notification when referred person donates (email: "Someone donated thanks to your share! Help us reach [goal]")
- [ ] Optional: Referrer dashboard showing their referrals and conversions
- [ ] Referral expiry: track referral for 30 days (donations within 30 days count)
- [ ] Analytics: GET /admin/referrals/analytics returns time series of referral conversions
- [ ] Data quality: validate ref parameter (must be valid UUID), sanitize before storing

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: generate share link with ref param, follow link, make donation, verify attribution
- [ ] Analytics calculated correctly
- [ ] Referral leaderboard tested
- [ ] Edge cases tested: invalid ref, expired referral, multiple referrals per user
- [ ] Deployed to staging and verified

## Technical Notes
- Generate short URL format for sharing (consider shortening via URL shortener)
- Store ref parameter in session before redirecting to destination
- Use middleware to capture and store referrer_user_id on donation/application
- Consider reward system for top referrers (gamification, future enhancement)
- Add privacy-aware logging for referral tracking
- Monitor for gaming the referral system (self-referrals, etc)

## Story Points: 5
