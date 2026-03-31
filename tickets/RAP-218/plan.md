# RAP-218 Plan

## Objective
Add open and click tracking for email campaigns via pixel and redirect endpoints.

## Acceptance Criteria
- [x] EmailCampaignEvent model with event_type (open/click), recipient_email, variant, ip/ua
- [x] Migration 086 for email_campaign_events table
- [x] Public pixel endpoint: GET /email-campaigns/track/open/{id} → 1x1 GIF
- [x] Public redirect endpoint: GET /email-campaigns/track/click/{id}?url=... → 302
- [x] Staff stats endpoint: GET /email-campaigns/{id}/stats → opens/clicks/rates
- [x] Unit tests for service functions (11 passing)
- [x] Integration tests for all endpoints (10 tests)

## Complexity Assessment
**Track**: Complex (new model + migration + service + API + tests across 6 files)

## Approach
Pixel tracking via 1x1 GIF, click tracking via redirect. Errors silently swallowed
at pixel/redirect endpoints to never break email display. Stats endpoint staff-only.
