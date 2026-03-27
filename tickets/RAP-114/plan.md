# RAP-114 Plan

## Objective
Add adoption request analytics showing time-to-decision, approval rate, and volume.

## Acceptance Criteria
- [x] GET /adoption-requests/analytics returns analytics data
- [x] Average time-to-decision in hours
- [x] Approval rate as percentage
- [x] Request volume for last 7 and 30 days
- [x] Status breakdown (pending/approved/rejected/cancelled)
- [x] Frontend analytics page with KPI cards and status breakdown
- [x] Analytics link from adoption request list page
- [x] Unit tests for schema and calculations

## Complexity Assessment
**Track**: Complex
- Backend analytics endpoint with SQL aggregation
- Frontend analytics page with multiple card types
- Schema validation tests
