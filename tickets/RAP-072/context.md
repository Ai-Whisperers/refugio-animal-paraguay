# RAP-072 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-27

## Current Focus
Implementing missing campaign features: featured flag, paused/archived status, photo_urls array, days_remaining in public response.

## Technical State
- Campaign model already exists in src/db/models/campaign.py
- Admin and public campaign endpoints already exist with core CRUD and progress
- Migration 013 created campaigns and campaign_donations tables
- Next migration is 016 (015 is sponsorships)
- All existing 38 campaign tests pass

## Next Steps
1. Write migration 016
2. Update ORM model
3. Update schemas
4. Update endpoints
5. Add tests

## Blockers
None

## Key Decisions Made
- Keep `cancelled` status for backward compat; add `paused` and `archived`
- `photo_urls` stored as ARRAY(TEXT) in PostgreSQL
- `days_remaining` computed at query time from deadline - now()
- Max 5 featured campaigns enforced at API level (warning, not hard block)
