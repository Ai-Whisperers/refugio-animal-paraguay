# RAP-261 Plan

## Objective
Add post-adoption follow-up schedule visibility and maintenance API (EPIC-53 S2).

## Acceptance Criteria
- [ ] get_due_follow_ups() service returns pending follow-ups due within N days
- [ ] get_overdue_follow_ups() service returns past-due pending follow-ups
- [ ] mark_overdue_follow_ups() bulk-updates pending past-due to OVERDUE status
- [ ] GET /api/admin/follow-ups/schedule/due endpoint
- [ ] GET /api/admin/follow-ups/schedule/overdue endpoint
- [ ] POST /api/admin/follow-ups/schedule/mark-overdue endpoint
- [ ] GET /api/admin/adoptions/{id}/follow-up-schedule endpoint
- [ ] Unit tests passing (80%+ coverage)

## Complexity Assessment
**Track**: Simple Fix — service functions + API wrapper
