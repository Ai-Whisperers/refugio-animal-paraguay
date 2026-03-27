# RAP-148 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-27

## Technical State
- `src/api/appointments.py` — GET /appointments and POST /appointments
- `src/schemas/appointments.py` — AppointmentCreate, AppointmentRow, AppointmentListResponse
- `src/app.py` — appointments_router registered
- `frontend/src/app/admin/appointments/page.tsx` — new appointments page with inline form
- `tests/unit/test_appointment_schemas.py` — 12 unit tests

## Key Decisions Made
- Reuses VetVisit model with visit_status=scheduled; no new DB table or migration needed
- GET endpoint filters to scheduled visits only by default; include_past=true shows past scheduled ones
- POST endpoint validates animal exists before creating the visit
- AppointmentRow includes animal_name and animal_species from join for better UX
