# RAP-030 Plan

## Objective
Build a staff admin panel frontend for managing animals and adoption requests.

## Description
The shelter staff need a web-based admin panel to manage animal records (create, edit, view, delete) and process adoption requests (view, approve, reject). This builds on the Next.js 14 scaffold (RAP-028) and connects to existing backend CRUD APIs. Requires JWT authentication with role-based access (staff/admin).

## Acceptance Criteria
- [ ] Staff can log in via email/password and receive JWT token
- [ ] Admin layout with sidebar navigation (Animals, Adoptions, Logout)
- [ ] Animals list page with pagination, species/status filters
- [ ] Animal create form with validation
- [ ] Animal edit form with pre-populated fields
- [ ] Animal delete with confirmation
- [ ] Adoption requests list with status filter
- [ ] Adoption request status transitions (approve/reject/cancel)
- [ ] Unauthenticated users redirected to login
- [ ] Role-based guard (only staff/admin can access admin pages)

## Complexity Assessment
**Track**: Complex Implementation

- Multiple files across types, layouts, components, and pages
- Auth context, API integration, forms with validation
- State management with SWR + React context

**Assessment result**: Complex — multi-page frontend feature with auth integration

## Approach
1. Add TypeScript types matching backend schemas
2. Create auth context provider (login/logout, token management)
3. Build admin layout with sidebar
4. Build login page
5. Build animals management (list + create/edit modals + delete)
6. Build adoption requests management (list + status update)
7. Lint and build validation

## Dependencies
- Depends on: RAP-028 (Next.js scaffold), RAP-003/004 (Animals CRUD API), RAP-006 (Adoption Request API), RAP-007 (JWT Auth)
- Blocked by: None

## Risks
- Risk: Backend APIs may not be running during frontend-only development → Mitigation: TypeScript types ensure contract, SWR handles loading/error states
