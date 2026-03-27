---
story: S5
epic: EPIC-84
ticket: RAP-570
title: "Share tracking analytics"
status: ready
points: 5
priority: P1
track: Backend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S5: Share tracking analytics

## Story
As an **admin**, I want **to track how content is being shared** so that **I can measure reach and engagement**.

## Description
Implement share event tracking to measure which content is most shareable and which platforms drive traffic. Provides analytics dashboard for share metrics.

## Acceptance Criteria
- [ ] ShareEvent model created: id (UUID), entity_type (enum: animal, campaign, story, blog_post), entity_id (UUID FK), platform (enum: whatsapp, facebook, twitter, copy_link, native_share), sharer_user_id (FK to User, nullable for anonymous), created_at (datetime)
- [ ] POST /api/shares/track endpoint created (public, no auth required, but logs IP)
- [ ] Request body: {entity_type, entity_id, platform}
- [ ] Each social share button click calls POST /api/shares/track before opening share dialog
- [ ] Response: {success: true} with 200 status
- [ ] Analytics dashboard at GET /admin/shares/analytics returns JSON with metrics
- [ ] Metrics include: total_shares (count), shares_by_platform (breakdown: whatsapp, facebook, twitter, copy_link), shares_by_entity_type (breakdown: animal, campaign, story, blog)
- [ ] Top shared animals: GET /admin/shares/analytics?entity_type=animal returns ranked list of animals by share count
- [ ] Top shared campaigns: GET /admin/shares/analytics?entity_type=campaign returns ranked list of campaigns by share count
- [ ] Time series data: shares per day for last 30 days (useful for trending)
- [ ] Share-to-donation conversion: track if sharer becomes donor within 7 days (requires user tracking, nice-to-have)
- [ ] Share-to-adoption conversion: track if sharer applies for animal within 30 days
- [ ] /admin/dashboard includes "Top Shared Content" widget showing most-shared animals/campaigns
- [ ] Rate limiting: prevent spam (max 10 track calls per minute per IP)
- [ ] Unit tests: verify share event creation, analytics aggregation

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: click share button, verify event tracked
- [ ] Analytics calculated correctly for test data
- [ ] Dashboard displays metrics correctly
- [ ] Rate limiting tested
- [ ] Deployed to staging and verified

## Technical Notes
- Use event sourcing pattern for immutable event logs
- Cache analytics results (recalculate hourly)
- Add indexes on entity_type, platform, created_at for efficient queries
- Consider Celery for background aggregation if volume is high
- Log IP for fraud detection (optional, privacy-aware)
- Monitor event tracking for data quality issues

## Story Points: 5
