# RAP-271 Plan

## Objective
Build a user activity timeline page showing all audit events for a specific user.

## Description
EPIC-55 S2 (P1). Page at `/admin/audit-logs/user/[userId]` renders a chronological timeline of all audit events for one user, using the existing `/admin/audit-logs?user_id=...` API.

## Acceptance Criteria
- [ ] Timeline page at `/admin/audit-logs/user/[userId]` renders per-user audit events
- [ ] Each entry shows: action label, resource type/ID, timestamp, IP address
- [ ] Change diff shown when old_values/new_values present
- [ ] Empty, loading, and error states handled
- [ ] Pagination for users with many events
- [ ] Tests passing (10/10)

## Complexity Assessment
**Track**: Simple Fix — frontend only, uses existing audit API

**Assessment result**: Simple Fix — new page using existing API + timeline pattern from AnimalHistoryTimeline
