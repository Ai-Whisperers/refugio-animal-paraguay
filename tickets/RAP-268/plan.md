# RAP-268 Plan

## Objective
Build an annual impact report backend endpoint backed by real DB queries, plus a frontend visualization page showing charts for key shelter metrics by month.

## Description
The `annual_report.py` service exists but returns placeholder data (all zeros). This ticket wires it to real database queries and adds a frontend admin page at `/admin/reportes/anual` with bar/line charts for monthly income, expenses, adoptions, and donations.

## Acceptance Criteria
- [ ] Backend: `/api/admin/reports/annual/{year}` returns real aggregated data from the DB
- [ ] Backend: Monthly breakdown shows income and expenses per month using Donation + FundAllocation models
- [ ] Backend: Donor metrics (total, new, recurring, average) populated from DB
- [ ] Backend: Animal outcomes (rescued, adopted) populated from DB
- [ ] Frontend: Admin page at `/admin/reportes/anual` with year picker
- [ ] Frontend: Charts rendered using Chart.js via canvas (no external CDN required)
- [ ] All edge cases handled (empty state, errors, permissions)
- [ ] Unit and integration tests passing

## Complexity Assessment
**Track**: Complex Implementation

- Multiple DB queries across several models
- Full-stack: backend service + API + frontend page + charts
- More than 3 files

**Assessment result**: Complex — backend DB wiring + frontend chart page

## Approach
1. Enhance `annual_report.py` service to accept a DB session and run real queries
2. Update `annual_reports.py` API router to inject DB session
3. Create frontend page `frontend/src/app/admin/reportes/anual/page.tsx` with charts

## Dependencies
- Depends on: RAP-265 (impact_report_service), RAP-266 (PDF service)
- Donation model, FundAllocation model, AdoptionRequest model, Animal model

## Risks
- Risk: DB schema may not have all needed fields → Mitigation: use existing models only
