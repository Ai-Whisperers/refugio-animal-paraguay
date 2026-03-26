# T02: Implement Profile Update Endpoint

## Frontmatter

- **task_id**: T02
- **story_id**: S03
- **epic_id**: EPIC-10
- **estimated_effort**: 5 story points
- **dependencies**: EPIC-10, S01-user-registration-and-login, T02-implement-login-endpoint, T01-implement-profile-retrieval
- **status**: Planned

---

## Task Summary

Implement a protected HTTP PATCH endpoint that allows authenticated users to update their own profile information. This endpoint modifies user-editable fields (name, phone, address) while preserving authentication credentials and account status. The update operation validates all input data, enforces business rules, and maintains audit trails.

---

## Why This Task Matters

User profile update is a fundamental capability in account management workflows. Users must be able to correct or change their contact information, address details, and other non-sensitive profile data. This task bridges registration and profile retrieval, completing the core profile management lifecycle. The update mechanism must be strictly guarded to prevent unauthorized modifications while remaining user-friendly. Proper input validation prevents data corruption and maintains system integrity.

---

## Technical Requirements

### Authentication Boundary

The profile update endpoint enforces strict authentication:

- Requires valid JWT Bearer token in Authorization header
- Token must be signed with HS256 and contain valid user ID claim
- Token expiration time must not have passed
- Revocation counter in payload must match current counter in database (prevents use of revoked tokens)
- Missing or malformed Authorization header returns 401 Unauthorized
- Invalid or expired token returns 401 Unauthorized
- Revoked token returns 401 Unauthorized

The authenticated user can only modify their own profile. Attempts to modify another user's profile via user ID in the request body are rejected with 403 Forbidden. The endpoint treats user ID as read-only and derives it from the authenticated token.

### Request Body Structure

The update request accepts a JSON object with optional fields:

- name: String, 1-255 characters, optional (if provided, must not be empty or whitespace-only)
- phone: String, 0-20 characters, optional (if provided, valid format required per Paraguayan standards, or null to clear)
- address: String, 0-500 characters, optional (if provided, basic length validation, or null to clear)

Fields not provided in the request are not modified. The endpoint does not accept email, password, or account status changes in this request (those use dedicated endpoints for security). Unknown fields in the request are ignored without error.

### Response Format

The successful response returns the complete updated user profile as a flat JSON object with snake_case field names:

- user_id: integer, immutable user identifier
- email: string, user's verified email address
- name: string, user's full name
- phone: string or null, user's phone number
- address: string or null, user's street address
- email_verified: boolean, whether email has been verified
- created_at: ISO 8601 timestamp string (UTC), account creation time
- updated_at: ISO 8601 timestamp string (UTC), profile last update time
- last_login_at: ISO 8601 timestamp string or null (UTC), most recent login timestamp

The response contains no authentication tokens, password data, or account status codes.

### HTTP Status Codes

- 200 OK: Update successful, response body contains updated profile
- 400 Bad Request: Input validation failed (field length, format, or required constraint)
- 401 Unauthorized: Missing, invalid, or expired token; or token revocation mismatch
- 403 Forbidden: Authenticated user attempting to modify another user's profile
- 404 Not Found: User profile not found (edge case during transaction)
- 500 Internal Server Error: Database or unexpected error

Error responses return structured JSON with error code and human-readable message. Generic error messages are used for security-sensitive failures to prevent information disclosure.

### Database Query Patterns

All database interactions use parameterized queries to prevent SQL injection:

- SELECT queries validate user existence and current profile state before update
- UPDATE queries modify only the specified fields: name, phone, address, and updated_at timestamp
- The query sets updated_at to current UTC timestamp automatically via database default or application logic
- All queries run within a transaction to ensure consistency
- Row-level locks are applied to prevent concurrent update conflicts
- Email field is never modified by this endpoint

The database stores phone and address as nullable string columns, allowing users to clear these fields by setting them to null in the request.

### Conflict Handling

Concurrent updates to the same profile may occur. The endpoint implements optimistic locking using a version field or updated_at timestamp:

- If concurrent update is detected (update_count mismatch or newer updated_at exists), return 409 Conflict with message indicating the conflict
- Alternatively, last-write-wins semantics can be applied if conflicting updates are acceptable
- Document which strategy is chosen in implementation notes

### Validation Rules

Input validation is strict and happens before database query:

- name: must be 1-255 characters, not empty, not pure whitespace
- phone: if provided and not null, must match Paraguayan phone format or be empty/null
- address: must be 0-500 characters if provided, or null to clear

The endpoint rejects requests with invalid data structures, such as arrays or nested objects in string fields.

---

## Implementation Approach

### Endpoint Definition

The endpoint is defined as a PATCH request to `/api/v1/auth/profile` (protecting against future breaking changes by versioning). The PATCH HTTP method semantics apply: the operation is partial, updating only specified fields. The endpoint accepts application/json content type.

### Dependency Injection

The endpoint uses FastAPI's dependency injection to obtain:

- Current authenticated user via the existing `get_current_user()` dependency, which validates the JWT token and returns the user object
- Database session for executing the update query
- Logging service for audit trail

### Request Validation

Pydantic v2 schema defines the request body with:

- Optional fields for name, phone, and address
- Field constraints (max length, format validators)
- Custom validators for phone format if needed

Schema validation occurs automatically before the endpoint handler executes.

### Response Construction

After the database update succeeds, the response constructs the complete user profile by:

- Querying the updated user record from the database to ensure consistency
- Mapping database columns to response field names (snake_case)
- Converting timestamps to ISO 8601 format
- Excluding password hash and sensitive internal fields

### Error Handling

Error handling follows these patterns:

- Validation failures (400): Pydantic automatically validates, returning structured errors for each field
- Authentication failures (401): Check token validity, expiration, and revocation status
- Permission failures (403): Verify authenticated user ID matches requested user ID
- Not found (404): If user record disappears during update (rare race condition)
- Conflict (409): If concurrent update detected
- Database errors (500): Log with full context, return generic error message

Invalid token or missing Authorization header triggers authentication failure before the handler executes, via the `get_current_user()` dependency.

### Audit Logging

Every successful profile update is logged with:

- User ID of the account modified
- User ID of the authenticated user performing the update (same in normal case)
- Timestamp of the update
- Fields that were changed (before/after values)
- IP address of the request (from headers or reverse proxy)
- User agent string

Audit logs are stored in a dedicated audit_log table with immutable append-only semantics.

### Testing Strategy

Unit tests verify:

- Input validation rejects invalid name (empty, too long, whitespace-only)
- Input validation rejects invalid phone format
- Input validation rejects invalid address (too long)
- Valid input passes validation
- Unknown fields are ignored
- Update modifies only specified fields, not others

Integration tests verify:

- Successful update with all fields provided
- Successful update with partial fields
- Successful update clearing phone and address to null
- Update fails with invalid token (401)
- Update fails with expired token (401)
- Update fails with revoked token (401)
- Update fails with missing Authorization header (401)
- Update fails when authenticated user attempts to modify another user (403)
- Updated profile is returned correctly in response
- Concurrent updates are handled correctly (conflict or last-write-wins)

End-to-end tests verify:

- Complete workflow: register user, login, retrieve profile, update profile, verify changes persisted
- User can update only their own profile, not others

---

## Acceptance Criteria

- [ ] PATCH endpoint `/api/v1/auth/profile` accepts JSON request body
- [ ] Request body schema defines optional name, phone, address fields
- [ ] name field validation: 1-255 characters, not empty or whitespace-only
- [ ] phone field validation: valid Paraguayan format or null
- [ ] address field validation: 0-500 characters or null
- [ ] Unknown fields in request are silently ignored
- [ ] Endpoint requires valid JWT Bearer token in Authorization header
- [ ] Missing Authorization header returns 401 Unauthorized
- [ ] Invalid token returns 401 Unauthorized
- [ ] Expired token returns 401 Unauthorized
- [ ] Revoked token returns 401 Unauthorized
- [ ] Authenticated user can only update their own profile
- [ ] Attempt to update another user's profile returns 403 Forbidden
- [ ] User ID is derived from token and cannot be modified by request
- [ ] Email field cannot be updated via this endpoint
- [ ] Password cannot be updated via this endpoint
- [ ] Account status cannot be modified via this endpoint
- [ ] Successful update returns 200 OK
- [ ] Response contains complete updated profile with all fields
- [ ] Response field names are in snake_case
- [ ] Response includes user_id, email, name, phone, address, email_verified, created_at, updated_at, last_login_at
- [ ] Timestamps in response are ISO 8601 formatted (UTC)
- [ ] Response contains no password hash or sensitive internal fields
- [ ] All database queries use parameterized queries (no string concatenation)
- [ ] Database transaction ensures consistency (all-or-nothing semantics)
- [ ] Concurrent update conflicts are detected and handled (409 or last-write-wins)
- [ ] Every successful update is logged to audit trail with all required fields
- [ ] Audit log includes user ID, timestamp, changed fields, IP address, user agent
- [ ] Database error returns 500 Internal Server Error with generic message
- [ ] Invalid request body returns 400 Bad Request with field-specific errors

---

## Definition of Done

- [ ] Code written: endpoint handler, request schema, response schema, audit logging
- [ ] Linting passes: zero linting errors or warnings (or justified suppressions)
- [ ] Type checking passes: 100% type coverage, zero type errors
- [ ] Tests written: unit tests for validation, integration tests for end-to-end scenarios
- [ ] Test coverage: minimum 80% line coverage for the endpoint
- [ ] All tests pass: no failures or skipped tests
- [ ] Database migrations applied: audit_log table exists with correct schema
- [ ] Security review: no SQL injection, no information disclosure, no unauthorized access
- [ ] Audit logging verified: sample request produces audit trail entry
- [ ] Documentation updated: API documentation includes endpoint definition, request/response examples
- [ ] Code reviewed: peer review completed, all comments resolved
- [ ] Deployed to staging: endpoint verified working in staging environment
- [ ] No regressions: existing tests still pass, no side effects on other endpoints
- [ ] Ready for production: all definition of done items checked, no known issues

