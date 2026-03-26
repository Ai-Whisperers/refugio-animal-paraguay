---
task_id: T01
task_title: Implement RBAC Dependency Factory
task_status: pending
story_id: S04
epic_id: EPIC-10
created_date: 2026-03-25
estimated_effort: 5
dependencies:
  - JWT authentication middleware (T02 from S01)
  - User model with role field
  - FastAPI dependency injection infrastructure
---

# T01: Implement RBAC Dependency Factory

## Overview

The RBAC dependency factory is a single reusable callable that FastAPI routers declare as a dependency. It accepts one or more role names and returns a FastAPI-compatible dependency function that, when injected into a route, extracts the JWT token from the Authorization header, decodes and verifies it using the application's JWT_SECRET, reads the role claim from the decoded payload, and compares the user's role against the list of roles permitted by that endpoint.

If the role is sufficient, the dependency resolves and execution continues into the route handler. If the role is insufficient, it raises HTTPException with 403 Forbidden. If the token is missing or invalid, it raises HTTPException with 401 Unauthorized.

## Why This Task Matters

Without a centralized RBAC mechanism, role checks would be scattered through every route handler as ad-hoc if-statements. This creates maintenance nightmares when roles change, enables logic errors where developers forget to add checks, and makes it impossible to audit which endpoints require what permission.

A centralized RBAC dependency factory enforces all role checks through a single, tested code path. FastAPI's dependency injection system is specifically designed for cross-cutting concerns like authentication — using it correctly means RBAC is declared once per router and inherited by all routes automatically. No route handler ever needs to remember to check permissions; the framework enforces it.

## Technical Requirements

### Core Factory Design

The dependency factory is a Python callable named `require_role` that accepts a variable number of role name strings as positional arguments and returns another callable — the actual FastAPI dependency. This inner callable is what FastAPI invokes during request processing.

The inner dependency function accepts the HTTP request's Authorization header as a string via FastAPI's Header parameter injection. It extracts the Bearer token from the Authorization header value by stripping the "Bearer " prefix (the standard format is "Bearer <token>").

### Token Processing

The token is decoded using PyJWT's decode function with the JWT_SECRET loaded from environment configuration and HS256 algorithm specification. The decoded payload dictionary must contain the user_id, role, iat (issued at), and exp (expiration) claims as defined in the JWT authentication middleware task.

### Role Validation Logic

The role claim value from the decoded payload is compared against the list of accepted roles passed to the factory when it was called. If the role is in the accepted list, the dependency returns the decoded payload dictionary so the route handler has access to the current user's identity and all claims.

If the role is not in the accepted list, the dependency raises HTTPException with status code 403 and detail message "Insufficient permissions". This communicates that the token is valid but the user lacks the required role.

### Error Handling

If the Authorization header is missing or malformed (does not follow the "Bearer <token>" format), raise HTTPException with status code 401 and detail message "Authentication required". This covers cases where the header is absent or lacks proper formatting.

If the token is expired, PyJWT raises ExpiredSignatureError when decode is called — catch this specific exception and raise HTTPException with status code 401 and detail message "Token expired". This allows clients to distinguish expired tokens and prompt re-authentication.

If the token signature is invalid (the signature does not match or the token was tampered with), PyJWT raises InvalidTokenError — catch this exception and raise HTTPException with status code 401 and detail message "Invalid token". Any token integrity issue results in rejection.

### Pre-built Convenience Aliases

Provide two pre-built convenience aliases that developers use instead of calling require_role directly for common cases:

The `require_admin_role` alias is created by calling require_role with "admin" only, restricting routes to administrators exclusively.

The `require_staff_role` alias is created by calling require_role with both "admin" and "staff" as accepted roles. This reflects the role hierarchy: staff members can access staff endpoints, and admin members can access staff endpoints as well since they have higher privileges.

### Module Organization

The factory function and both convenience aliases live in a shared auth module (named something like `auth.py` or `auth/rbac.py` in the application structure) so all routers import from the same location. This ensures consistency and makes it trivial to update RBAC logic globally.

## Implementation Approach

### Closure Pattern

Conceptually, the factory pattern works as follows: the outer function `require_role` closes over the roles list, capturing it in a closure. It returns the inner function, which FastAPI calls automatically during request processing. Each time `require_role` is called, it creates a new closure with a specific set of allowed roles, enabling multiple RBAC dependencies with different role requirements to coexist in the same application.

### FastAPI Dependency Injection

FastAPI's `Depends()` annotation on router instantiation or individual routes triggers the dependency machinery. When a route has a dependency, FastAPI calls that dependency function before invoking the route handler. The dependency can return a value (the decoded payload) which becomes an argument passed to the handler function.

### Router-level Dependencies

When `require_staff_role` is added as a dependency to a FastAPI APIRouter instance via the `dependencies` parameter, every route registered on that router automatically requires the staff role without any per-route annotation. This is the key architectural benefit: a developer adding a new route to a protected router immediately gets RBAC enforcement.

### Decoded Payload in Handlers

The decoded payload dictionary returned by the dependency becomes an argument in route handlers that declare it as a parameter. For example, if a route handler declares a parameter named `current_user`, and the dependency is named such that it can be matched to this parameter, the handler receives the decoded JWT payload containing user_id, role, and other claims.

## Success Criteria and Testing Strategy

### Unit Testing

Unit tests should mock PyJWT's decode function to return payloads with various role values. Tests must verify that the dependency raises 403 for wrong roles (when the user's role is not in the accepted list), 401 for expired and invalid tokens, and successfully resolves the decoded payload for correct roles. Each error condition should be tested independently.

The `require_admin_role` and `require_staff_role` aliases must be tested independently to confirm they work as expected. For example, a test ensures that `require_admin_role` accepts "admin" but rejects "staff", while `require_staff_role` accepts both "admin" and "staff".

### Integration Testing

Integration tests should make real HTTP requests with tokens actually signed with the test secret to verify end-to-end behavior. These tests create valid JWT tokens with different role values, send them in Authorization headers, and confirm that the endpoint responds with 200 for allowed roles, 403 for insufficient roles, and 401 for missing or invalid tokens.

A test verifying that router-level dependencies block all routes registered on a protected router is required. This ensures that if a developer adds a new route to a protected router, that route is automatically protected without requiring explicit action.

### Manual Verification

An OpenAPI specification page (generated automatically by FastAPI) should show security requirements for each endpoint. After implementing this task, security badges should appear on protected endpoints, indicating the required role levels.

## Acceptance Checklist

- The `require_role` factory callable exists and accepts variable positional arguments for role names
- The factory returns a callable suitable for FastAPI Depends() usage
- The inner dependency extracts and validates JWT tokens from the Authorization header
- Role validation logic correctly checks if the user's role is in the accepted list
- HTTPException with 403 is raised for insufficient permissions
- HTTPException with 401 is raised for missing, malformed, expired, or invalid tokens
- `require_admin_role` alias exists and restricts to "admin" only
- `require_staff_role` alias exists and permits both "admin" and "staff"
- All code lives in a shared auth module for central management
- Unit tests cover all error conditions and role combinations
- Integration tests verify end-to-end behavior with real tokens
- OpenAPI documentation reflects security requirements
