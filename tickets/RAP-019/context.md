# RAP-019 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26

## Current Focus
Starting implementation of InKindDonation model and migration.

## Technical State
- Donor model exists in src/db/models/donation.py with donations relationship
- Latest migration on develop is 004_add_donors_and_donations.py
- Need migration 005 for in_kind_donations table

## Next Steps
1. Add ItemType enum and InKindDonation model to donation.py
2. Create migration 005
3. Add schemas and API endpoints

## Blockers
None

## Key Decisions Made
- Store estimated_value as integer cents (consistent with Donation.amount_cents)
- Reuse existing CurrencyCode enum
- Staff-only access for all in-kind donation endpoints
