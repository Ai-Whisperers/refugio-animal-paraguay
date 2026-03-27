# RAP-121 Plan

## Objective
Add role-based menu visibility to the admin sidebar so staff and admin users see appropriate navigation items.

## Description
The admin sidebar currently shows the same navigation items to all authenticated users. Admin users need access to additional items (Settings, User Management) that staff users should not see. The sidebar should read the user's role from the JWT token and filter nav items accordingly.

## Acceptance Criteria
- [ ] Staff users see only permitted menu items (Dashboard, Animals, Adoptions, Donors, Donations)
- [ ] Admin users see all menu items including Settings and User Management
- [ ] Navigation gracefully handles missing/invalid role (defaults to staff-level visibility)
- [ ] No admin-only routes are exposed in the sidebar for staff users

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files
- [x] Change impact ≤10 lines of actual code
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Simple Fix — single component modification, well-understood pattern of role-based filtering

## Approach
1. Add optional `requiredRole` field to `NavItem` interface (undefined = visible to all)
2. Add admin-only nav items (Settings, User Management) with `requiredRole: "admin"`
3. Import `getCurrentUserRole()` and filter NAV_ITEMS based on current role
4. Handle edge case where role is null (unauthenticated or invalid token)

## Dependencies
- Depends on: RAP-120 (Admin sidebar component) — PR #106

## Risks
- Risk: RAP-120 not yet merged → Mitigation: branch from RAP-120 branch, PR will note dependency
