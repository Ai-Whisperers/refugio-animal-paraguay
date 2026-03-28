# RAP-536 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-28 10:44

## Current Focus
N/A — ticket complete.

## Technical State
- Migration 070 added rescuer_id, goal_message, animal_ids, requires_approval to campaigns table
- Service: src/services/rescuer_campaign_service.py — auto-approval logic, donation aggregation
- API: src/api/rescuer_campaigns.py — portal + public routers registered in app.py
- Frontend: portal campaigns page + public campaign detail page
- Tests: 15 unit + 8 integration all pass

## Next Steps
N/A — delivered in PR #299.

## Blockers
None.

## Key Decisions Made
- Extended campaigns table instead of new table — consistent with staff campaign model
- Auto-approval: is_verified → active; not verified → draft + requires_approval=True
- Donation aggregation via target_type/target_id (no campaign_id field on Donation)

## RESUME POINT
N/A — COMPLETED
