# RAP-144 Plan

## Objective
Add a surgical statistics dashboard showing surgery counts by type, status, and outcome with success rates.

## Description
Staff need aggregate insight on surgery outcomes. This page fetches all surgeries and computes client-side statistics: counts by status/type/outcome, success rate, complication rate.

## Acceptance Criteria
- [ ] Staff can navigate to /admin/surgeries/stats
- [ ] Page shows total surgery count
- [ ] Page shows success rate (% of completed surgeries with successful outcome)
- [ ] Page shows complication rate (% of all surgeries with complications status)
- [ ] Page shows bar charts: by status, by type, by outcome
- [ ] Empty state shown when no surgeries exist

## Complexity Assessment
**Track**: Frontend

**Assessment result**: Simple Fix — pure frontend aggregation page, no new backend endpoints needed.

## Approach
- Fetch GET /surgeries?size=500
- Compute stats client-side (aggregation helpers)
- Render stat cards + CSS bar charts (no external chart library)
- Link from surgery schedule page header

## Dependencies
- Depends on: RAP-142 (GET /surgeries endpoint)
