---
task_id: T02
task_title: Apply RBAC to All API Routers
task_status: pending
story_id: S04
epic_id: EPIC-10
created_date: 2026-03-25
estimated_effort: 6
dependencies:
  - T01-implement-rbac-dependency (require_role factory must exist)
  - All router modules for each epic's endpoints
---

# T02: Apply RBAC to All API Routers

## Overview

With the RBAC dependency factory built, this task applies it systematically to every API router across the application. Each router module is reviewed and the appropriate dependency alias is added to the APIRouter instantiation. The task involves examining each router's purpose, determining which role level it requires, and applying the dependency at router creation.

The public portal router for EPIC-11 endpoints explicitly receives no role dependency since it serves unauthenticated visitors. The admin router requires require_admin_role. The staff-accessible animal, adoption, medical, and volunteer routers receive require_staff_role. The adopter profile router receives a custom require_role call that permits the adopter role explicitly. After completion, every single endpoint in the application has documented and enforced access control, with zero unprotected routes except those explicitly declared public.

## Why This Task Matters

Adding RBAC at the router level rather than per-route is the correct architectural pattern for FastAPI applications because it eliminates the possibility of forgetting to protect a new route. When a developer adds a new endpoint to the admin router, that route automatically gets RBAC enforcement without requiring any extra steps or additional annotations. The protection is inherited.

This task closes all authorization gaps by systematically auditing every router in the application and confirming its protection status. Any router left unprotected becomes a security vulnerability — a potential entry point for unauthorized access. This task ensures that the final state of the application has zero unprotected routes except those explicitly declared public for legitimate reasons.

Without this systematic approach, protection would be inconsistent. One team member might remember to add checks to sensitive routers, another might not. Over time, as new routers are added, inconsistency grows. The systematic application ensures uniform security policy across the entire application.

## Router Protection Matrix

The following table defines the RBAC requirement for each router in the application:

| Router Module | Purpose | Protection Level | Allowed Roles | Rationale |
|---|---|---|---|---|
| Public Portal Router | Display animal listings, content pages, donation campaigns for public visitors | None (Public) | N/A | Unauthenticated visitors must view this content without login |
| Auth Router | User registration, login, password reset, email verification, token refresh | None (Public) | N/A | These routes are the entry points to authentication; allowing them is required for users to register and log in |
| Adopter Profile Router | Adopters manage their own profile data, view applications, track approvals | Custom require_role | adopter, staff, admin | Adopters access their own profile; staff and admin can view any profile for oversight |
| Adoption Application Router | Adopters submit applications, view application status; staff process applications | Custom require_role | adopter, staff, admin | Adopters submit and track applications; staff process them |
| Animal Management Router | Staff CRUD operations for animal records, intake data, medical flags | require_staff_role | staff, admin | Only staff and above can manage animal data; public cannot see creation/modification of internal data |
| Medical Records Router | Staff view and update medical history, vaccination records, health notes | require_staff_role | staff, admin | Medical data is sensitive; only staff can access |
| Volunteer Management Router | Volunteer registration, availability scheduling, task assignments | require_staff_role | staff, admin | Staff manages volunteers and task allocation |
| Admin Users Router | List users, modify user roles, disable accounts, view user activity logs | require_admin_role | admin | Only administrators can manage user accounts and roles |
| Admin Settings Router | Modify application settings, email templates, donation configurations | require_admin_role | admin | Only administrators can change system configuration |
| Admin Reporting and Export Router | Generate reports, export data, view analytics | require_admin_role | admin | Sensitive reporting and data export restricted to admin |
| Donations Admin Router | View donations, generate receipts, track donor relationships | require_admin_role | admin | Financial data access restricted to administrators |
| Notification Management Router | View notification history, test notification channels, modify notification settings | require_staff_role | staff, admin | Staff manages notifications for adopters and volunteers |

## Technical Requirements

### Router Dependencies Parameter

When creating an APIRouter instance, the dependencies parameter accepts a list of Depends() wrappers around the dependency function. Each Depends() call wraps the appropriate dependency (require_admin_role, require_staff_role, or a custom require_role call). Every route registered on that router automatically inherits those dependencies and runs them before the route handler executes.

For example, the admin router initialization includes dependencies=[Depends(require_admin_role)]. Any route registered on this router will run the admin role check before executing. A developer adding a new endpoint to the admin router gets this protection automatically without thinking about it.

### Custom Role Requirements

Some routers require non-standard role configurations. The adopter profile router accepts three roles: adopter (users of the platform), staff (staff members who can view all profiles), and admin (administrators who can view all profiles). This is created by calling require_role("adopter", "staff", "admin") directly instead of using a pre-built alias.

The adoption application router similarly accepts require_role("adopter", "staff", "admin") since adopters submit applications and staff process them.

These custom calls are defined once at the router level and reused consistently.

### Verification Through OpenAPI Documentation

After applying dependencies to all routers, FastAPI automatically generates OpenAPI specification documentation that reflects these requirements. Visiting the OpenAPI schema (typically at /openapi.json or the Swagger UI at /docs) shows security requirements for each endpoint. Every protected endpoint will display its required roles. Every public endpoint will be documented as public.

A developer or security auditor can review this documentation to confirm that every endpoint has appropriate protection status. This provides visual verification that the protection is correctly configured.

### Object-Level Ownership Checks

While RBAC dependency answers "can this role type access this endpoint", some endpoints require additional checks for object-level ownership. For example, an adopter should only be able to access their own profile, not other users' profiles. An adoption application submitted by one adopter should not be visible to another adopter.

These object-level ownership checks are separate from RBAC and live inside route handler implementations. After the RBAC dependency passes and the route handler begins executing, the handler extracts the user_id from the decoded JWT payload (passed as a parameter to the handler) and compares it against the resource's owner_id. If they do not match, the handler raises HTTPException with 403 Forbidden.

This two-layer approach is standard in secure API design: RBAC handles role-level access control (the horizontal permission), and ownership checks handle user-level data isolation (the vertical permission). Both are necessary; neither alone is sufficient.

## Implementation Approach

### Audit Process

A developer implementing this task should follow a systematic audit process:

First, list every router module in the application. For FPUNA Refugio Animal Paraguay, routers correspond to Epic task groups: EPIC-11 for public portal, EPIC-12 for auth, EPIC-13 for adopter management, EPIC-14 for adoption workflow, EPIC-15 for animal management, EPIC-16 for medical, EPIC-17 for volunteering, EPIC-18 for admin users, EPIC-19 for admin settings, EPIC-20 for admin reporting, EPIC-21 for donations, and EPIC-22 for notifications.

Second, for each router, identify its purpose. Is it for public access, staff operations, or admin functions?

Third, determine the appropriate protection level from the Router Protection Matrix above.

Fourth, modify the router instantiation to include the dependencies parameter with the appropriate dependency.

Fifth, document the protection level in comments next to the router instantiation for future maintainers.

### Integration Testing Strategy

Integration tests verify that dependencies are actually enforced. These tests make real HTTP requests to each endpoint with three different authorization states: no token (Authorization header absent), wrong role token (a valid JWT with insufficient role), and correct role token (a valid JWT with the required role).

For each endpoint, the test framework should:

Send a request with no Authorization header and verify the response is 401 Unauthorized. This confirms that authentication is required.

Send a request with an Authorization header containing a valid JWT with a role that is not in the endpoint's allowed list (for example, sending an adopter role to an admin-only endpoint) and verify the response is 403 Forbidden. This confirms that role validation works correctly.

Send a request with an Authorization header containing a valid JWT with an allowed role and verify the response is 200 or the appropriate success code (201 for creation, 204 for deletion, etc.). This confirms that properly authenticated and authorized requests succeed.

These tests should run against actual running instances of the API to confirm end-to-end behavior. They verify that the dependency injection is properly wired and that role checking works as designed.

### Router-Level Dependencies Verification

A specific test should confirm that router-level dependencies apply to all routes on that router. This test creates a protected router with require_admin_role, registers multiple routes on it with different implementations, and verifies that every single route responds with 401 or 403 to unauthorized requests. This proves that if a developer adds a new route to a protected router, that route is automatically protected.

### Documentation and Comments

For each router, add comments documenting the protection status:

For public routers, document that this router is intentionally public. For example, a comment above the public portal router instantiation states "This router serves unauthenticated visitors and is intentionally public."

For protected routers, document the required role. A comment above the admin router states "This router requires admin role; all endpoints automatically reject non-admin users."

For routers with custom role requirements, specify the roles. A comment above the adopter profile router states "This router accepts adopter, staff, and admin roles; adopters can access their own data while staff/admin can access any data."

These comments serve as inline documentation for future maintainers.

## Special Handling and Edge Cases

### Public Routes on Protected Routers

It is uncommon but sometimes necessary to have one public route (no auth required) on a router that is otherwise protected. This is achieved by adding a public parameter to the specific route when registering it. For example, if a staff router has one endpoint that should be public, that endpoint is registered with skip_dependency=True or a similar mechanism. This should be done only when absolutely necessary and must be documented.

### Anonymous User Context

Some routes might accept either authenticated or unauthenticated requests, providing different responses based on authentication state. For example, a donations list endpoint might show limited public information to unauthenticated users but detailed information to authenticated donors. This requires a slightly different dependency pattern: the dependency returns None if the Authorization header is missing (rather than raising 401), and route handlers check if the user context is None. This is also uncommon and should be implemented only when explicitly required.

### Token Refresh Endpoint

The token refresh endpoint accepts an expired token (which would normally be rejected) to generate a new token. This endpoint cannot use the standard authentication dependency that rejects expired tokens. Instead, it must have custom logic that explicitly allows expired tokens. This is a special case documented in the auth router implementation.

## Success Criteria

After completing this task, the application must meet the following criteria:

All endpoints must have documented protection status. Every endpoint in the application falls into exactly one of three categories: explicitly public (no authentication required), explicitly protected with a specific role requirement (named via require_admin_role, require_staff_role, or require_role call), or explicitly ownership-checked after RBAC passes (role check plus user_id comparison inside handler).

The OpenAPI documentation must reflect these requirements. Running the FastAPI application and visiting the OpenAPI schema shows security requirements for every endpoint. Public endpoints are documented as having no security requirement. Protected endpoints show the required roles.

An end-to-end test suite must verify that each router responds correctly to requests with no token (401 Unauthorized unless public), wrong role token (403 Forbidden unless public), and correct role token (200 or appropriate success code). Tests cover at least one endpoint from each router to ensure comprehensive coverage.

No unprotected routes exist except those explicitly documented as public. A manual audit or automated scan confirms that every sensitive endpoint has RBAC protection applied.

Comments in the code document the protection status of each router, explaining why it requires or does not require authentication.

## Acceptance Checklist

- Public portal router has no authentication dependency and is documented as public
- Auth router (registration, login) has no authentication dependency and is documented as public
- Adopter profile router has require_role("adopter", "staff", "admin") applied
- Adoption application router has require_role("adopter", "staff", "admin") applied
- Animal management router has require_staff_role applied
- Medical records router has require_staff_role applied
- Volunteer management router has require_staff_role applied
- Admin users router has require_admin_role applied
- Admin settings router has require_admin_role applied
- Admin reporting router has require_admin_role applied
- Donations admin router has require_admin_role applied
- Notification management router has require_staff_role applied
- All routers have comments documenting protection status
- OpenAPI documentation correctly shows security requirements
- Integration tests verify that 401 is returned for missing tokens
- Integration tests verify that 403 is returned for insufficient roles
- Integration tests verify that 200 is returned for authorized requests
- Ownership checks are implemented in handlers where required (adopter profile, adoption applications)
- No unprotected endpoints remain except explicitly documented public routes
