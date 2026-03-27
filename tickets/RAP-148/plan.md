# RAP-148 Plan

## Objective
Add appointment scheduling for vets: cross-animal view of scheduled vet visits with ability to create new appointments.

## Description
Staff and vets need to see all upcoming scheduled vet visits and create new ones without navigating to specific animal records. This provides a calendar-style overview and a scheduling form.

## Acceptance Criteria
- [x] GET /appointments lists all scheduled vet visits with animal info
- [x] POST /appointments creates a new scheduled vet visit
- [x] Frontend page shows upcoming appointments ordered by date
- [x] Toggle to include past scheduled appointments
- [x] Form to create a new appointment (animal ID, vet name, date, type, reason)
- [x] Animal link navigates to /admin/animals/{id}?tab=medical

## Complexity Assessment
**Track**: Simple Fix

**Assessment result**: Simple Fix — new endpoints wrapping existing VetVisit model; frontend list + form page.

## Approach
- Backend: New `appointments.py` router with GET (list scheduled visits) and POST (create scheduled visit)
- Frontend: `/admin/appointments` page with list and inline creation form
- No new DB migration needed — VetVisit model already supports scheduled status

## Dependencies
- VetVisit model (existing)
- Animal model (existing)
- require_medical_staff auth dependency (existing)
