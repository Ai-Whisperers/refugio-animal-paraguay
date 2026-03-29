# RAP-254 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-29 00:00

## Current Focus
Implementing CSV export endpoints for operational dashboard data.

## Technical State
- Pattern: StreamingResponse with io.StringIO + csv.writer (from donations.py)
- Two endpoints: /export/metrics and /export/population
- Auth: require_staff (same as other endpoints)

## Next Steps
1. Add export helper functions to service
2. Add export endpoints to router
3. Write unit tests

## Blockers
None
