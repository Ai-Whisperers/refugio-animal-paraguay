# RAP-642 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-28 14:35

## Current Focus
Implementing volunteer onboarding checklist and training status.

## Technical State
- Build on existing VolunteerProfile (volunteer_profiles table)
- New table: volunteer_onboarding_items
- Migration: 073

## Next Steps
1. Create model + migration
2. Add to volunteer.py router (staff init + mark endpoints)
3. Add volunteer GET endpoint
4. Create frontend onboarding page
5. Write tests

## Blockers
None
