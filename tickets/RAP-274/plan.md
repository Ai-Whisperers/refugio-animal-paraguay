# RAP-274 Plan

## Objective
Implement a data change history viewer page that shows all audit log entries for a specific resource, with expandable before/after diffs.

## Description
Part of EPIC-55 S5. Staff need to trace the full change history of any specific resource (animal, adopter, donation, etc.) by navigating to a dedicated page filtered by resource_type and resource_id. Each entry shows the action, user, timestamp, and an expandable side-by-side diff of changed fields.

## Acceptance Criteria
- [x] Dynamic route `/admin/audit-logs/resource/[resourceType]/[resourceId]` renders the change history page
- [x] Page title "Historial de Cambios" is displayed
- [x] Resource type and resource ID shown in header
- [x] Loading state while fetching
- [x] Error state with retry button on API failure
- [x] Empty state when no entries exist
- [x] Timeline entries show action badge, user ID, timestamp, IP, request_id
- [x] "Ver cambios" button visible for entries with old_values or new_values
- [x] Clicking "Ver cambios" expands diff showing Antes/Despues columns with changed fields only
- [x] Pagination shown when total > page_size
- [x] API called with resource_type and resource_id as query params

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files
- [x] Change impact ≤10 lines of actual code
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Simple Fix — pure frontend, new dynamic route page, no schema or backend changes needed. Uses existing `/admin/audit-logs` API with resource_type + resource_id query params.

## Approach
Create `frontend/src/app/admin/audit-logs/resource/[resourceType]/[resourceId]/page.tsx` as a Client Component. Reuse the `AuditLogEntry` type from `@/types/api`. DiffViewer subcomponent computes changed keys by comparing old_values vs new_values. ChangeEntry subcomponent handles expand/collapse state.

## Dependencies
- Depends on: Existing GET `/api/v1/admin/audit-logs` endpoint (RAP-270 S1 infrastructure)

## Risks
- None — isolated new page, no shared state mutations
