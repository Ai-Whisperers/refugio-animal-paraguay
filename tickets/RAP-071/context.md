# RAP-071 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26 20:08

## Current Focus
Implementing animal sponsorship tiers & matching — ORM models, migration, schemas, API routes, tests.

## Technical State
- Branch: feature/RAP-071-animal-sponsorship-tiers (to be created)
- New files: src/db/models/sponsorship.py, src/db/alembic/versions/014_create_sponsorships.py, src/schemas/sponsorship.py, src/api/sponsorships.py
- App.py requires router registration
- Stripe mock: used in integration tests via monkeypatch

## Next Steps
1. Create sponsorship ORM models
2. Create Alembic migration
3. Create Pydantic schemas
4. Create API router
5. Register in app.py
6. Write tests

## Blockers
None

## Key Decisions Made
- Tier pricing in cents: Bronze=1000, Silver=2500, Gold=5000 (USD)
- Sponsorship status enum: active, paused, cancelled, completed
- Stripe mock pattern: monkeypatch stripe module in integration tests (matches existing pattern)
