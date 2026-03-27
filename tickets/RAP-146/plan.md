# RAP-146 Plan

## Objective
Add a vet-specific dashboard page showing today's appointments, pending results, and overdue vaccinations.

## Description
Veterinarians need a focused view showing what needs immediate attention: surgeries scheduled for today, in-progress surgeries with complications, and vaccination alerts. This is a read-only dashboard aggregating data from existing surgery and vaccination APIs.

## Acceptance Criteria
- [x] Log in as vet and see today's scheduled surgeries
- [x] See surgeries currently in-progress and any with complications
- [x] See overdue and upcoming vaccination alerts
- [x] Refresh button to reload data
- [x] Navigation links to detailed pages (surgeries, vaccination alerts)

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files
- [x] Frontend-only, uses existing APIs
- [x] Low risk of side effects

**Assessment result**: Simple Fix — Frontend page only, uses existing `/surgeries` and `/vaccination-alerts` endpoints.

## Approach
Commit the existing vet-dashboard page.tsx implementation which was created but never committed.

## Dependencies
- RAP-145 (vet role) — done
- Surgeries API — done
- Vaccination alerts API — done
