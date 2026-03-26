---
story_id: S04
epic_id: EPIC-10
title: "Role-Based Access Control (RBAC)"
estimated_effort: 11
status: Planned
---

# S04: Role-Based Access Control (RBAC)

## Story Summary

Implement a role-based access control system that enforces permissions across all API endpoints. The system defines three distinct role tiers—admin, staff, and adopter—with hierarchical authorization rules. This story establishes the RBAC middleware, permission decorators, and access control patterns that protect sensitive endpoints and operations, ensuring users can only perform actions their role permits.

## Why This Story Matters

Without role-based access control, any authenticated user could access any endpoint and perform any action. This creates catastrophic security vulnerabilities: adopters could delete animals, access donor records, or modify staff accounts. RBAC is the foundational security layer that enforces the principle of least privilege across the entire API. Every endpoint must declare its required role(s) and the system must validate permissions on every request. This story establishes that enforcement mechanism.

## Acceptance Criteria

- [ ] Role enumeration defined with three tiers: admin, staff, adopter
- [ ] Role hierarchy is explicitly documented: admin > staff > adopter
- [ ] RBAC middleware component created and integrated into FastAPI request pipeline
- [ ] Decorators or route guards enable simple role requirement declaration on endpoints
- [ ] Permission check occurs before any endpoint logic executes
- [ ] Unauthorized access returns 403 Forbidden with generic error message
- [ ] Role information is extracted from JWT token payload and validated
- [ ] Role cannot be modified by client request—only stored in token and database
- [ ] All existing authentication endpoints declare their required role(s)
- [ ] RBAC enforcement is testable via unit and integration tests
- [ ] Documentation explains role hierarchy and usage patterns
- [ ] No hardcoded role checks scattered throughout codebase (centralized only)
- [ ] Performance impact of permission checks is negligible (<5ms per request)

## Technical Context

The RBAC system operates at two enforcement points: within JWT tokens and in database records. When a user authenticates, their role is included in the JWT payload and signed by the server. On each request, the middleware extracts the role from the token, verifies the signature, and checks whether the user's role satisfies the endpoint's requirements. The database maintains the source of truth for user roles; changes to a user's role take effect when their token is refreshed or reissued.

Role hierarchy means that higher tiers inherit permissions of lower tiers. An admin user can perform all actions an adopter can perform, plus admin-exclusive actions. This reduces permission declaration complexity and prevents logical inconsistencies where adopter-exclusive actions accidentally require higher roles.

Three roles cover Refugio's organizational structure. Admin users manage staff accounts, system configuration, and sensitive operations. Staff users handle daily shelter operations: animal intake, medical records, adoption approvals, and volunteer coordination. Adopter users submit adoption applications, view available animals, and manage their profile.

## Definition of Done

- [ ] RBAC middleware component implemented
- [ ] Role enumeration defined in shared constants
- [ ] Permission decorators/route guards created and documented
- [ ] All authentication endpoints updated with role requirements
- [ ] Unit tests verify permission checks with all role combinations
- [ ] Integration tests verify role enforcement across request pipeline
- [ ] End-to-end tests verify unauthorized access returns 403
- [ ] Code review completed and approved
- [ ] No linting errors, type errors, or test failures
- [ ] Test coverage meets minimum threshold (80%)
- [ ] Security audit confirms no privilege escalation vulnerabilities
- [ ] Documentation updated with RBAC usage guide
- [ ] Performance benchmarks confirm <5ms overhead per request
- [ ] Staging deployment completed and tested
- [ ] Product owner sign-off obtained
- [ ] Ready for integration with downstream features

## Related Stories

- **S01 (User Registration & Login)**: Establishes authentication foundation; RBAC validates the authenticated user's role
- **S02 (Password Reset & Email Verification)**: Relies on RBAC to restrict password reset endpoint to unauthenticated users only
- **S03 (Profile Management)**: Applies RBAC to profile endpoints (users can only modify their own profile)
- **S05 (Animal Intake & Records)**: Will require RBAC to restrict to staff role only
- **S06 (Adoption Management)**: Will require RBAC to enforce adopter-specific and staff-specific workflows

## Estimated Effort Justification

Story points: 11 (medium-complex)

This story is larger than individual profile management tasks because it spans the entire API surface and affects all downstream features. The work includes:

1. **RBAC Middleware Architecture** (3 points): Design and implement the middleware component that intercepts requests, extracts roles, and validates permissions
2. **Permission Decorators/Guards** (2 points): Create reusable decorators/route guards that enable simple `@require_role("admin")` syntax on endpoints
3. **Role Enumeration & Hierarchy** (1 point): Define the three roles and their hierarchical relationships
4. **Integration with Existing Endpoints** (2 points): Update all authentication endpoints to declare their role requirements
5. **Testing & Validation** (2 points): Comprehensive unit, integration, and end-to-end tests covering all role combinations
6. **Documentation & Performance Verification** (1 point): Write usage guide and benchmark RBAC overhead

## Story Points Breakdown

| Component | Points | Rationale |
|-----------|--------|-----------|
| Middleware design & implementation | 3 | Core request pipeline integration |
| Permission decorators | 2 | Reusable pattern across all endpoints |
| Role definition & hierarchy | 1 | Documentation + enumeration |
| Endpoint integration | 2 | Apply RBAC to existing auth endpoints |
| Testing | 2 | Comprehensive coverage of permission checks |
| Documentation & benchmarks | 1 | Usage guide + performance verification |
| **Total** | **11** | **Medium-complexity story** |

## Success Metrics

- [ ] All API endpoints either declare a role requirement or explicitly accept any authenticated user
- [ ] No endpoint allows unauthenticated access except registration, login, password reset, and email verification
- [ ] 100% of protected endpoints return 403 for users lacking required role
- [ ] No privilege escalation possible via token manipulation or header injection
- [ ] RBAC middleware performance overhead is documented and verified <5ms
- [ ] All team members understand and follow RBAC patterns in subsequent features
