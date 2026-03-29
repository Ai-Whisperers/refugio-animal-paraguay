# RAP-272 Plan

## Objective
Add CSV and JSON export functionality for audit logs, reusing the existing backend export endpoint.

## Acceptance Criteria
- [ ] ExportAuditLogsButton component triggers download in CSV or JSON format
- [ ] Export page at /admin/audit-logs/export with format selector and filters
- [ ] Filters (action, resource_type, start_date, end_date) applied to export
- [ ] Loading state during download
- [ ] Error state on failure
- [ ] 15 tests passing

## Complexity Assessment
**Track**: Simple Fix — new component + page, backend endpoint already exists
