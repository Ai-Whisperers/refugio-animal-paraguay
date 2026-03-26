# RAP-037 References

## Story
- `planning/epics/EPIC-14-sponsorship-and-campaigns/stories/S01-animal-sponsorship-tiers/STORY.md`

## Key Files
- `src/db/models/sponsorship.py` — Sponsorship ORM model (new)
- `src/schemas/sponsorship.py` — Pydantic schemas (new)
- `src/services/sponsorship_service.py` — Business logic (new)
- `src/api/sponsorships.py` — API router (new)
- `src/api/webhooks.py` — Extended for subscription events
- `src/db/alembic/versions/011_add_sponsorships.py` — Migration (new)

## Patterns
- SEPA mandate pattern (RAP-036): similar lifecycle model
- Stripe SDK v15: `[]` access on StripeObject
- Webhook handler pattern in `src/api/webhooks.py`
