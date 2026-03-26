---
task_id: T02
task_title: Implement Role Editor
task_status: pending
story_id: S02
epic_id: EPIC-7
created_date: 2026-03-25
estimated_effort: 4
dependencies:
  - T01 user management UI (user listing must exist)
  - EPIC-10 RBAC (require_admin_role)
  - users table with role column
---

# T02: Implement Role Editor

## Overview

The role editor provides the PATCH endpoint for modifying user roles. This is a focused, deliberately narrow endpoint: it accepts only the new role value and returns the updated user record. Role changes take effect immediately in the database but do not invalidate existing JWTs — users with outstanding tokens retain their old role until token expiry, which is an accepted trade-off documented in the system design.

## Why This Task Matters

Shelter staff get promoted to admin, volunteers are onboarded as adopters first, donors need their accounts upgraded to staff to help manage operations. Without a role management endpoint, role changes require direct database access, which is operationally risky and inaccessible to non-technical admin users. This endpoint enables self-service role management through the admin dashboard, removing developer bottlenecks from routine operational tasks.

## Technical Requirements

The PATCH endpoint accepts a path parameter user_id identifying which user's role will be changed, and a JSON request body containing a single field: role. The role field must be one of exactly three valid role strings: the string "admin", the string "staff", or the string "adopter". Pydantic validation rejects any role value not in this set with a 422 unprocessable entity response that lists the three valid options in the error message for clarity.

An admin user cannot change their own role through this endpoint as a safety measure — if the user_id in the URL path matches the authenticated admin's user_id extracted from the JWT payload, the endpoint returns 403 forbidden with a clear message stating "Cannot change your own role". This prevents an admin from accidentally revoking their own admin privileges.

If the target user_id specified in the path does not exist in the users table, the endpoint returns 404 not found. The endpoint then updates the role column on the users table row identified by user_id to the new role value. The response returns the full updated user record with the same shape as the user listing response from T01 story for consistency, with the new role value visible.

All role changes are recorded in an audit log table with the following fields populated: admin_user_id identifying who performed the change, target_user_id identifying whose role changed, previous_role containing the role value before the change, new_role containing the role value after the change, and timestamp showing when the change occurred.

The require_admin_role dependency must be present on this endpoint, meaning only authenticated users with admin role can invoke it.

## Implementation Approach

The endpoint function receives user_id as a path parameter of type UUID and the validated role body model containing the single role field. It first queries the users table to confirm the target user exists, raising 404 not found if the query returns no rows. It then checks that the user_id in the path does not match the current admin's user_id extracted from the JWT dependency payload, returning 403 if they match.

The function reads the current role value for the target user before performing any modifications, storing it in a local variable for use in the audit log. It then updates the role column on the users table row, persisting the change with a database commit. The audit log entry is written in the same database transaction as the role update to ensure atomicity — if either the role update or audit log write fails, both operations roll back together and the user sees an error.

The response serializes the updated user record using the same Pydantic response model as the user listing endpoint from T01 to maintain consistency across admin interfaces. This ensures that admin UI components expecting a particular user record shape across endpoints do not need different handling logic.

## Success Criteria

Changing a user's role to a new valid value must be reflected immediately when the user listing endpoint is queried. The user record in listing responses must show the new role. Attempting to change one's own role must be blocked with 403 forbidden response. Attempting to assign an invalid role string like "supervisor" must return 422 with a clear validation error listing the three valid options. Attempting to change a non-existent user must return 404 not found.

Audit log entries must exist for every successful role change with complete information: admin_user_id, target_user_id, previous_role, new_role, and timestamp. Tests must cover successful role change from adopter to staff, from staff to admin, and vice versa. Tests must verify self-role-change is blocked. Tests must verify invalid role values are rejected. Tests must verify non-existent user_id is rejected.
