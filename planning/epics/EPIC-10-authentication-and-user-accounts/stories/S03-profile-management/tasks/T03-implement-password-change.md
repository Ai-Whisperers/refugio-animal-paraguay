---
task_id: T03
story_id: S03
epic_id: EPIC-10
estimated_effort: 4
status: Planned
priority: High
dependencies:
  - EPIC-10
  - S01-user-registration-and-login
  - T02-implement-login-endpoint
  - T01-implement-profile-retrieval
---

# T03: Implement Password Change Endpoint

## Task Summary

Implement a protected HTTP POST endpoint that allows authenticated users to change their own password. The endpoint must validate the current password, enforce new password requirements, revoke existing JWT tokens to force re-authentication, maintain audit logs, and follow the same security standards established in the login and password reset flows.

## Why This Task Matters

Users need a secure, self-service mechanism to change their password without going through the password reset flow. This endpoint strengthens account security by requiring knowledge of the current password before allowing a new one, preventing unauthorized password changes in cases of compromised sessions. It is essential for user account autonomy and security compliance.

---

## Technical Requirements

### Authentication Boundary

The endpoint must require a valid, non-revoked JWT Bearer token in the Authorization header. The token's signature must be verified using the HS256 algorithm with the server's secret key. The token's expiration timestamp must not have passed. The token's revocation counter embedded in the claims must match the user's current revocation counter in the database, blocking access if the user has invalidated their previous sessions. Absence of a valid token returns HTTP 401 Unauthorized.

### Request Body Structure

The request body must be a JSON object containing two required fields: current_password (a string of 1 to 128 characters representing the user's existing password) and new_password (a string that must differ from current_password, meet length requirements of 8 to 128 characters, contain at least one uppercase letter, at least one lowercase letter, at least one digit, and at least one special character from the defined set). Both fields are required; omitting either returns a 400 Bad Request validation error.

### Response Format

A successful password change returns HTTP 200 OK with a JSON response containing a single status field set to "password_changed_successfully", a message field with user-friendly confirmation text, and a timestamp field indicating when the change occurred. The response does not include sensitive data or the user's profile information. Failed requests return appropriate HTTP status codes with error details but no information about password strength, hashing mechanisms, or token revocation logic.

### HTTP Status Codes

HTTP 200 OK indicates successful password change. HTTP 400 Bad Request indicates missing fields, validation failures on new_password (length, character requirements), or identical current and new passwords. HTTP 401 Unauthorized indicates missing, malformed, or expired JWT token, or revocation counter mismatch. HTTP 403 Forbidden should not occur for password change (users always have permission to change their own password). HTTP 404 Not Found indicates the authenticated user account no longer exists (edge case of deleted account). HTTP 409 Conflict should not occur unless concurrent password change requests are attempted (advisory only). HTTP 500 Internal Server Error indicates database or cryptographic operation failures.

### Database Query Patterns

The implementation must query the user record by user_id extracted from the JWT claims using a parameterized query that prevents SQL injection. The current password verification must compare the provided current_password against the user's hashed password using bcrypt's comparison function with constant-time semantics to prevent timing attacks. Password verification failure must not reveal whether the user account exists. The new password must be hashed using bcrypt with a minimum cost factor of 12, taking 100 to 200 milliseconds per hash to resist brute force attacks. All updates must be wrapped in a database transaction ensuring atomicity: if the password hash update fails, the revocation counter increment does not occur. After successful password change, the user's revocation counter must be incremented atomically within the same transaction, invalidating all existing JWT tokens issued prior to this change.

### Token Revocation Strategy

When a user changes their password, all existing JWT tokens must be invalidated immediately to force re-authentication. The implementation achieves this through a revocation counter embedded in the JWT claims at token creation time. When verifying a token, the claims' revocation counter is compared against the user's current revocation counter in the database; if they differ, the token is rejected as revoked. Incrementing the revocation counter in the database immediately upon password change invalidates all previous tokens without maintaining a blacklist. This strategy is stateless and scalable, avoiding the need for token blacklists or scheduled cleanup tasks.

### Validation Rules

The new_password field must be between 8 and 128 characters in length, contain at least one uppercase letter (A-Z), contain at least one lowercase letter (a-z), contain at least one numeric digit (0-9), and contain at least one special character from the set: ! @ # $ % ^ & * ( ) - _ = + [ ] { } ; : ' " , . < > ? /. Password requirements are enforced through custom validators that provide specific feedback about which requirements are not met. Passwords must not be a commonly-breached password (checked against a predefined list or breach database). Password must not be identical to the user's previous password(s) from the last N password changes (where N is a configurable parameter, typically 3 to 5). The current_password must exactly match the user's stored password hash; no fuzzy matching is permitted.

---

## Implementation Approach

### Endpoint Definition

The endpoint is defined as POST /api/v1/auth/password-change with Content-Type: application/json. The endpoint path indicates an action-oriented endpoint (change) distinct from the profile update endpoint (PATCH /api/v1/auth/profile). The POST method is semantically correct for actions that modify server state, even though the change is scoped to the authenticated user's own account. The endpoint is protected by the same JWT authentication middleware used by other protected endpoints.

### Dependency Injection

The endpoint handler receives the following injected dependencies: get_current_user(), a dependency function returning the authenticated User object or raising an HTTPException if the token is invalid, expired, or revoked; database session, providing transactional access to the user repository; password_service, a utility for hashing and comparing passwords using bcrypt; revocation_service, a utility for incrementing revocation counters; audit_logger, a service for recording password change events with user ID, timestamp, IP address, user agent, and success/failure status; and configuration, providing bcrypt cost factor and password breach database location.

### Request Validation

The endpoint defines a Pydantic v2 schema for the request body containing current_password and new_password fields with constraints and custom validators. The new_password validator calls password_strength_validator() which checks length, character composition, and breach database membership. The validator returns specific error messages such as "Password must contain at least one uppercase letter" to guide users. The current_password validator is minimal (required field only); actual validation occurs during password comparison to avoid revealing user existence through timing differences.

### Password Verification and Update

The implementation queries the user record by user_id from the JWT token using a parameterized query. The password_service.compare() method performs constant-time comparison of the provided current_password against the user's stored password_hash using bcrypt. If comparison fails, the endpoint returns HTTP 400 Bad Request with a generic message ("Current password is incorrect") without revealing whether the user account exists. If current_password matches, the implementation hashes the new_password using bcrypt with cost factor 12 (or higher), producing a new password_hash. The password_hash update and revocation_counter increment are executed within a database transaction to ensure atomicity.

### Revocation Counter Increment

Within the same transaction as the password update, the user's revocation_counter is incremented by 1. This atomicity ensures that if the database connection fails after the password is hashed but before the counter is incremented, the entire transaction rolls back and the password change is not persisted. The revocation_service provides an atomic increment operation that is safe for concurrent updates (using SQL UPDATE statements that increment in-place, not read-modify-write patterns). After the transaction commits, all JWT tokens issued prior to the password change are invalidated because their embedded revocation_counter will no longer match the user's current_counter.

### Audit Logging

The audit_logger records password change events with the following details: user_id from the JWT claims, timestamp of the change, IP address extracted from the X-Forwarded-For or remote address, user agent from the request headers, outcome (success or failure with reason), and old password hash (never stored, but a hash of the hash could be logged for integrity verification). Audit logs are written to a protected log file or database table with restricted read access. Failed password change attempts (current password incorrect, validation failure) are also logged to detect brute force attacks or suspicious behavior patterns.

### Error Handling

Validation failures on new_password return HTTP 400 Bad Request with an errors field listing specific validation failures such as "Password must contain at least one uppercase letter". Current password mismatch returns HTTP 400 Bad Request with a generic message to avoid user enumeration. Missing current_password or new_password returns HTTP 400 Bad Request. Invalid or expired JWT token returns HTTP 401 Unauthorized. Token with mismatched revocation counter returns HTTP 401 Unauthorized. User account deletion (edge case) returns HTTP 404 Not Found. Database transaction failures or bcrypt failures return HTTP 500 Internal Server Error with a generic message and detailed logging for administrators.

### Testing Strategy

Unit tests verify password validation logic independently: testing minimum length enforcement, character composition requirements, breach database membership, and rejection of passwords identical to current password. Unit tests verify bcrypt cost factor and constant-time comparison behavior. Integration tests verify the complete endpoint flow with a real database: successful password change with valid current password, failed password change with incorrect current password, failed password change with weak new_password, and verification that subsequent requests with old tokens (pre-revocation) are rejected while new tokens (after revocation counter increment) are accepted. End-to-end tests verify the endpoint through HTTP requests: successful password change followed by logout and re-login with new password, concurrent password change requests from multiple sessions, and session invalidation after password change.

---

## Acceptance Criteria

- [ ] Endpoint POST /api/v1/auth/password-change implemented and routed correctly
- [ ] Endpoint requires valid, non-revoked JWT Bearer token in Authorization header
- [ ] Token signature verified using HS256 algorithm and server secret key
- [ ] Token expiration checked; expired tokens return HTTP 401
- [ ] Revocation counter in token claims matched against user's database counter; mismatch returns HTTP 401
- [ ] Request body schema defined in Pydantic v2 with current_password and new_password fields
- [ ] current_password field is required; omission returns HTTP 400
- [ ] new_password field is required; omission returns HTTP 400
- [ ] new_password length validated: minimum 8 characters, maximum 128 characters
- [ ] new_password must contain at least one uppercase letter (A-Z)
- [ ] new_password must contain at least one lowercase letter (a-z)
- [ ] new_password must contain at least one numeric digit (0-9)
- [ ] new_password must contain at least one special character from defined set
- [ ] new_password identical to current_password rejected with specific error message
- [ ] new_password compared against common breach database; breached passwords rejected
- [ ] new_password not identical to user's last N previous passwords (N configurable, default 3)
- [ ] Custom validators provide specific feedback on password requirement failures
- [ ] User record queried by user_id from JWT token using parameterized query
- [ ] current_password compared against user's hashed password using bcrypt constant-time comparison
- [ ] Password mismatch returns HTTP 400 with generic message (no user enumeration)
- [ ] new_password hashed using bcrypt with minimum cost factor 12
- [ ] Password hashing takes 100-200 milliseconds to resist brute force attacks
- [ ] Password hash update and revocation counter increment wrapped in database transaction
- [ ] Transaction atomicity ensures both operations succeed or both roll back
- [ ] Revocation counter incremented by 1 within transaction using atomic SQL UPDATE
- [ ] After password change, all existing JWT tokens become invalid
- [ ] Successful password change returns HTTP 200 OK
- [ ] Response includes status field set to "password_changed_successfully"
- [ ] Response includes message field with user-friendly confirmation text
- [ ] Response includes timestamp field indicating change time
- [ ] Response does not include sensitive data or profile information
- [ ] Audit log entry created recording password change event
- [ ] Audit log includes user_id, timestamp, IP address, user agent, success/failure status
- [ ] Failed password change attempts logged to detect brute force attacks
- [ ] HTTP 400 returned for validation failures with specific error messages
- [ ] HTTP 401 returned for missing, malformed, or expired JWT token
- [ ] HTTP 401 returned for revocation counter mismatch
- [ ] HTTP 404 returned if authenticated user account no longer exists
- [ ] HTTP 500 returned for database or cryptographic operation failures with generic message
- [ ] Unit tests verify password validation logic in isolation
- [ ] Unit tests verify bcrypt cost factor and constant-time comparison
- [ ] Integration tests verify complete endpoint flow with real database
- [ ] Integration tests verify token revocation after password change
- [ ] Integration tests verify old tokens rejected after revocation counter increment
- [ ] End-to-end tests verify password change through HTTP requests
- [ ] End-to-end tests verify re-login with new password after change
- [ ] End-to-end tests verify concurrent password change request handling
- [ ] All tests pass with zero failures and no skipped tests
- [ ] Code coverage for endpoint and password utilities at or above 85%
- [ ] No hardcoded credentials, API keys, or secrets in code
- [ ] No log output of passwords, hashes, or sensitive authentication details
- [ ] Error responses do not leak information about password hashing or token mechanisms
- [ ] Endpoint documented in API specification with request/response examples
- [ ] Endpoint documented in user-facing help or account management guide
- [ ] Code follows established linting standards with zero warnings
- [ ] Code uses type hints on all function signatures and parameters
- [ ] Code follows naming conventions established in project (snake_case functions, camelCase config)
- [ ] Code is reviewed and approved by at least one team member
- [ ] Code is merged to develop branch only after all CI/CD checks pass
- [ ] Code includes comments explaining non-obvious security decisions
- [ ] Implementation handles edge cases: concurrent requests, deleted user accounts, database failures
- [ ] Performance tested: endpoint responds within SLA (< 500ms p95 latency)

---

## Definition of Done

- [ ] All acceptance criteria above marked complete and verified
- [ ] Unit test suite passes: `pytest tests/unit/test_password_change.py`
- [ ] Integration test suite passes: `pytest tests/integration/test_password_change_flow.py`
- [ ] End-to-end test suite passes: `pytest tests/e2e/test_password_change_e2e.py`
- [ ] Code coverage at or above 85%: `pytest --cov=src/auth --cov-fail-under=85`
- [ ] Linting passes with zero warnings: `ruff check src/auth/`
- [ ] Type checking passes with zero errors: `mypy src/auth/`
- [ ] Security scanning clean: `bandit -r src/auth/ --severity-level medium`
- [ ] No hardcoded secrets or credentials detected: `detect-secrets scan src/auth/`
- [ ] Code follows Google Python style guide conventions
- [ ] Documentation updated: API spec, user guide, security considerations
- [ ] Peer review approval obtained from backend team member
- [ ] Commit message follows conventional commits format: `feat(auth): implement password change endpoint`
- [ ] Pull request created, title: "EPIC-10 S03 T03: Implement Password Change Endpoint"
- [ ] Pull request description links to task ticket and lists related acceptance criteria
- [ ] All CI/CD checks passing: linting, type checking, security scan, test suite
- [ ] Code merged to develop branch only after approval and green CI/CD status
- [ ] Deployment procedure documented for release/x.y.z branch merge
- [ ] Monitoring and alerting configured for password change endpoint errors
- [ ] Runbook created for troubleshooting password change failures
- [ ] No breaking changes to API contract; version unchanged (still v1)
- [ ] Performance benchmarks show endpoint responds within SLA
