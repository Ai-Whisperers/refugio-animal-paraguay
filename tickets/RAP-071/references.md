# RAP-071 References

## Key Files
- src/db/models/sponsorship.py (new)
- src/db/models/donation.py (reference: Donor model)
- src/db/models/campaign.py (reference: Campaign pattern)
- src/db/models/animal.py (reference: Animal model)
- src/db/alembic/versions/014_create_sponsorships.py (new)
- src/schemas/sponsorship.py (new)
- src/api/sponsorships.py (new)
- src/app.py (register router)
- tests/unit/test_sponsorship_models.py (new)
- tests/integration/test_sponsorships.py (new)

## Reference Patterns
- src/api/in_kind_donations.py — staff-only CRUD pattern
- src/api/donations.py — Stripe integration pattern
- src/db/alembic/versions/013_create_campaigns_table.py — migration pattern
- src/schemas/donation.py — schema pattern
