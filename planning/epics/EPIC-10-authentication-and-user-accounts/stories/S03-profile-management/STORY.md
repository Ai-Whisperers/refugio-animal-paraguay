---
story_id: S03
story_title: Profile Management
estimated_effort: 10
dependencies:
  - S01-user-registration-and-login
status: pending
---

# S03: Profile Management

## Story Description

As an authenticated user (adopter, staff, or admin), I want to manage my user profile so that I can maintain accurate personal information, change my password independently from reset flows, and verify my account status.

## Why This Story Matters

User profile management is essential for account maintenance and user autonomy. Users need the ability to view their current profile information, update personal details like name, phone, and address, change their password when desired (distinct from emergency password reset), and understand their account verification status. Without profile management capabilities, users would be stuck with information they provided at registration time and unable to correct errors or update contact details. Additionally, a dedicated password change endpoint for authenticated users provides better UX than requiring password reset flows for routine password rotation.

## Story Overview

This story covers four key profile management capabilities: retrieving authenticated user profile information without exposing sensitive data, updating profile fields with validation and audit logging, changing password for authenticated users with security protections, and exposing account verification status. Each capability is protected by authentication and authorization checks ensuring users can only access and modify their own profiles. All profile changes are logged in the audit trail for security monitoring.

## Technical Scope

### Profile Retrieval

Authenticated users retrieve their complete profile information via a protected endpoint. The endpoint requires valid JWT token authentication and returns the current user's profile data. The response includes personal information (name, email, phone, address, role), account status (email_verified, account_created, last_login), and role information. Sensitive information like password hashes, reset tokens, and verification tokens are never exposed in profile responses.

### Profile Update

Users update profile fields through a protected endpoint accepting JSON request body with fields to modify. Updatable fields include full name, phone number, and street address. The email address is never updatable through this endpoint, preventing users from changing their login email without verification. Updates are validated through Pydantic schemas ensuring phone numbers match reasonable formats (international E.164 format or simple numeric), addresses are non-empty strings under 500 characters, and full names are non-empty strings under 200 characters. Each update is logged in the audit trail with user identification, timestamp, fields modified, and IP address. The endpoint returns the updated profile with all changes reflected.

### Password Change

Authenticated users change their password through a protected endpoint distinct from the password reset flow. Password change is available only to authenticated users with valid JWT tokens. The endpoint requires the current password for verification to prevent unauthorized password changes if an attacker gains temporary access to an unlocked device. The endpoint validates the current password using bcrypt comparison against the stored hash. If the current password is invalid, the endpoint returns HTTP 401 Unauthorized with a generic error message. The new password must meet the same strength requirements as password reset (minimum 12 characters, at least one uppercase letter, at least one lowercase letter, at least one digit, at least one special character), but also must be different from the current password. The endpoint hashes the new password with bcrypt at cost factor minimum 12, updates the user password and revocation counter in an atomic database transaction, and invalidates all existing JWT tokens by incrementing the token revocation counter. This ensures that compromised tokens cannot be used after a password change. The endpoint returns HTTP 200 with a generic success message and sends an optional password change confirmation email asynchronously.

### Account Status

The profile response includes clear account status information indicating whether the email address has been verified. This allows users to understand whether they can perform actions restricted to verified accounts. Unverified users receive guidance indicating they need to verify their email address before accessing certain features.

## Acceptance Criteria

* The profile retrieval endpoint is protected by JWT authentication requiring a valid, non-expired token with matching token revocation counter
* The profile endpoint returns HTTP 401 Unauthorized if no token is provided or if the token is invalid, expired, or revoked
* The profile response includes all personal information fields (name, email, phone, address, role) with accurate current values
* The profile response includes account status fields (email_verified, account_created, last_login, created_at) with accurate values
* Sensitive information fields like password hash, salt, reset tokens, verification tokens, and revocation counter are never exposed in the profile response
* The profile update endpoint is protected by JWT authentication requiring a valid token
* The profile update endpoint accepts JSON request body with optional fields for name, phone, and address
* Profile updates are validated through Pydantic schemas with length constraints (name under 200 characters, address under 500 characters, phone in E.164 format or simple numeric)
* The email address cannot be modified through the profile update endpoint and is silently ignored if provided
* Each successful profile update is logged in the audit trail with user identification, timestamp, fields modified, and IP address
* The profile update endpoint returns HTTP 200 with the updated profile data reflected
* The password change endpoint is protected by JWT authentication requiring a valid token
* The password change endpoint accepts current password and new password via JSON request body
* The current password is validated using bcrypt comparison against the stored hash with constant-time comparison preventing timing side channels
* Invalid current password returns HTTP 401 Unauthorized with generic error message without revealing the mismatch
* New password must meet strength requirements (minimum 12 characters, uppercase, lowercase, digit, special character)
* New password must be different from current password to prevent circumventing security
* New password is hashed with bcrypt at cost factor minimum 12 before storage
* Password change updates both password hash and token revocation counter in an atomic transaction
* All existing JWT tokens for the user are invalidated by incrementing the revocation counter, preventing token reuse after password change
* Password change returns HTTP 200 with generic success message
* Password change attempts with invalid current password are logged in the audit trail
* Successful password changes send optional confirmation email asynchronously via FastAPI BackgroundTasks
* All profile endpoints use parameterized database queries preventing SQL injection
* All profile data is returned in consistent JSON format with consistent field names
* All profile endpoints return proper HTTP status codes (200 success, 400 malformed request, 401 unauthorized, 403 forbidden, 404 not found, 500 server error)
* All error messages are generic and do not reveal sensitive information about account state

## Story Points: 10

## Dependencies

This story depends on S01-user-registration-and-login being complete to establish the authentication infrastructure. The JWT token system, bcrypt password hashing, database schema with user accounts table, and email delivery system must all be in place before profile management can be implemented.

## Definition of Done

* All three tasks (T01-implement-profile-retrieval, T02-implement-profile-update, T03-implement-password-change) are complete with all acceptance criteria verified
* All profile management endpoints return proper HTTP status codes and error messages
* All sensitive information is excluded from profile responses
* All profile changes are logged in the audit trail with proper context
* All database operations use parameterized queries
* All endpoints have integration tests covering happy paths, edge cases, and security scenarios
* All code passes linting with zero warnings
* All code passes type checking with zero errors
* Code coverage for profile management module is above 90%
* Documentation is updated with profile management endpoint specifications
* PR includes all changes with clear commit messages referencing ticket ID
