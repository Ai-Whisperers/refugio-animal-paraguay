# RAP-270 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-29 00:00

## Current Focus
Building frontend audit log viewer page and sidebar link.

## Technical State
- Backend API: GET /admin/audit-logs (paginated, filterable) — exists in src/api/admin.py
- Backend export: GET /admin/audit-logs/export?format=csv|json — exists
- Frontend: No audit-logs page exists yet
- Pattern: Follow donors/donations admin page conventions

## Next Steps
1. Create frontend/src/app/admin/audit-logs/page.tsx
2. Update AdminSidebar with "Registros de Auditoria" nav item
3. Write tests

## Blockers
None

## Key Decisions Made
- Use existing admin page pattern (donors page as reference)
- Spanish labels following project convention
- Filter by: action, resource_type, start_date, end_date (most useful for staff)
