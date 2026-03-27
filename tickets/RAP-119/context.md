# RAP-119 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-27 09:10

## Current Focus
Implementing GET /donors list endpoint with search, filters, pagination, and CSV export.

## Technical State
- Donors router at src/api/donors.py has POST and GET /{id} only
- Donations router has established list+export pattern to follow
- DonorResponse schema already exists

## Next Steps
1. Add list endpoint to donors router
2. Add CSV export endpoint
3. Write tests
