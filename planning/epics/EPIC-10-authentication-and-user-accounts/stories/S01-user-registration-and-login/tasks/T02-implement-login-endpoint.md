# T02: Implement Login Endpoint

---

**task_id**: T02
**task_title**: Implement Login Endpoint
**task_status**: pending
**story_id**: S01
**epic_id**: EPIC-10
**created_date**: 2026-03-25
**estimated_effort**: 5 story points
**dependencies**:
- T01 (User registration endpoint must exist first)
- Database schema with user table must be in place
- Bcrypt password verification utilities must be available
- JWT token generation utilities must be functional

---

## Overview

The login endpoint serves as the authentication gateway for all users of the Refugio Animal Paraguay system. This endpoint accepts user credentials (email and password) and, upon successful validation, returns a JSON Web Token that grants access to protected resources. The login endpoint is critical for establishing authenticated sessions that allow users to interact with adoption requests, donation records, volunteer schedules, and administrative functions. Unlike the registration endpoint which creates new user accounts, the login endpoint validates existing credentials against stored password hashes and issues tokens that encode user identity and authorization scope. The endpoint must handle both successful authentication and multiple failure scenarios with appropriate HTTP status codes and error messages that guide users toward resolution without exposing sensitive information about whether email addresses are registered in the system.

The implementation of the login endpoint requires careful attention to security boundaries, rate limiting, and error handling. Attackers frequently target login endpoints with credential stuffing attacks, brute-force attempts, and timing attacks. The implementation must include mechanisms to detect and slow down repeated failed authentication attempts while maintaining a responsive experience for legitimate users. The endpoint must also carefully manage information disclosure, avoiding patterns that allow attackers to enumerate valid email addresses by observing differences in error messages or response times between valid and invalid accounts.

## Why This Task Matters

User authentication is the foundation of all access control in the Refugio Animal Paraguay system. Without a properly implemented login endpoint, the platform cannot establish user identity for any subsequent operation. The login endpoint directly impacts user experience because every interaction with the system begins with successful authentication. Users attempting to access their adoption applications, view donation history, schedule volunteer shifts, or perform administrative functions must first authenticate through the login endpoint. A slow, confusing, or unreliable login endpoint creates friction that discourages platform adoption.

Beyond user experience, the login endpoint is a critical security boundary. This is where the system validates that users are who they claim to be. If the login endpoint fails to properly verify credentials, enforce password requirements, or rate-limit failed attempts, attackers can gain unauthorized access to user accounts. Compromised accounts enable attackers to manipulate adoption records, redirect donation funds, impersonate volunteers, or access confidential shelter data. The security posture of the entire system depends on the login endpoint correctly validating credentials, issuing tokens only for verified users, and maintaining audit trails of authentication events.

The login endpoint also establishes the authentication pattern used throughout the system. How tokens are issued, what claims they contain, and how they are validated in downstream services all follow the patterns established here. Inconsistencies or weaknesses in the login endpoint architecture become security problems across every protected endpoint in the system.

## Technical Requirements

The login endpoint must accept HTTP POST requests containing email address and plaintext password. The request payload structure should include an email field containing a user's registered email address and a password field containing the plaintext password provided by the user. The endpoint must not accept GET requests, OPTIONS requests, or other HTTP methods; only POST is valid for authentication attempts.

Email validation during login must be case-insensitive for the lookup operation. User database queries should normalize the email address to lowercase before searching, ensuring that users can authenticate using any case variation of their registered email. The database query must be parameterized to prevent SQL injection, and the query should return the user record only if a matching email exists; if no user with that email is found, the endpoint must not reveal this fact through different error messages or response times.

Password validation requires comparing the plaintext password from the request against the bcrypt hash stored in the user database. The comparison operation must use bcrypt's verification function, which safely compares the input password against the stored hash without timing attacks. The bcrypt function should never fail or throw exceptions during the comparison; it should always return a boolean result indicating match or mismatch. If the hash comparison returns false, indicating the password does not match the stored hash, the endpoint must reject the login attempt.

Upon successful credential validation, the endpoint must issue a JWT token using the HS256 (HMAC with SHA-256) signing algorithm. The token must be signed using a secret key stored securely in environment variables, never embedded in code or version control. The JWT payload must include specific claims: the sub claim containing the user's unique identifier (UUID), the role claim containing the user's authorization level (adopter, staff, or admin), the iat claim containing the issued-at timestamp, and the exp claim containing the token expiration timestamp. The token expiration time should be set to one hour from the issued-at time, creating an access token with reasonable lifetime that requires users to re-authenticate periodically for security.

The response for successful authentication must use HTTP 201 Created status code and return a JSON object containing the issued token. The response object should include a token field with the JWT string, a token_type field set to "Bearer" indicating the authentication scheme, and an expires_in field containing the token lifetime in seconds. The response may optionally include the user object containing non-sensitive user data such as user_id, email, first_name, last_name, and role, allowing the frontend to populate user interface elements without requiring an additional API call.

Error handling must cover multiple failure scenarios with appropriate HTTP status codes. If the request body is malformed, missing required fields, or fails schema validation, the endpoint must return HTTP 400 Bad Request with an error message describing what validation failed. If the email address is not found in the database or the password does not match the stored hash, the endpoint must return HTTP 401 Unauthorized with a generic error message such as "Invalid email or password" that does not distinguish between the two failure modes. Returning an identical error for both invalid email and invalid password prevents attackers from determining which email addresses are registered in the system. If the login attempt succeeds but a server error occurs while generating the token, the endpoint must return HTTP 500 Internal Server Error with a generic error message.

Rate limiting must be implemented to prevent brute-force attacks. The endpoint should track failed authentication attempts per email address and per IP address, implementing progressively longer delays after repeated failures. After three failed attempts within a five-minute window for a specific email address, the endpoint should impose a one-second delay. After five failed attempts, impose a five-second delay. After ten failed attempts, lock the account for fifteen minutes, requiring the user to initiate a password reset. The rate limiting must not interfere with legitimate users who mistype their passwords occasionally, but it must make automated attack attempts economically unfeasible.

Audit logging must record all authentication attempts, both successful and failed. Successful login events should log the user ID, email address, timestamp, IP address, and user agent string. Failed login attempts should log the attempted email address, timestamp, IP address, user agent, and reason for failure (invalid password, user not found, account locked, rate limit exceeded). Audit logs must be written to a secure location with restricted access, never exposed through API responses or error messages.

## Implementation Approach

The login endpoint implementation begins with defining a Pydantic schema for the login request. The schema should have two required fields: email with string type and email validator, and password with string type. The email field should be validated to confirm it is a properly formatted email address. The password field should accept any non-empty string without imposing additional validation, since password requirements are enforced during registration.

The endpoint function should accept the login request through dependency injection, receiving the Pydantic model instance. The function should also accept database session and configuration dependencies, making these available from FastAPI's dependency system. The function should be declared as async to align with FastAPI's async-first design pattern.

Within the endpoint function, the first operation normalizes the email address to lowercase and queries the user database. The query should use parameterized statements through SQLAlchemy's ORM, filtering by the lowercase email address. If no user record is found, the endpoint should not immediately return an error; instead, it should proceed to the password comparison step but use a dummy hash for comparison. This prevents timing attacks where the response time reveals whether an email is registered.

Password verification compares the plaintext password from the request against the hash retrieved from the database (or a dummy hash if the user was not found). The bcrypt verify function returns a boolean indicating whether the passwords match. If the user was not found or the password does not match, the endpoint should record the failed attempt in the audit log with the IP address and timestamp, check the rate limiting table to see if the account or IP has exceeded the failure threshold, and return HTTP 401 Unauthorized with the generic error message.

If the credentials are valid, the endpoint should generate a JWT token. The token generation process creates a payload dictionary with the required claims: sub set to the user's UUID as a string, role set to the user's role, iat set to the current Unix timestamp, and exp set to one hour in the future. The JWT library signs this payload using the HS256 algorithm with the secret key from environment configuration. The signed token is returned as a string.

The endpoint should record the successful authentication in the audit log, clearing any rate limiting penalties for this user or IP address. The endpoint returns an HTTP 201 response with a JSON body containing the token, token_type set to "Bearer", and expires_in set to 3600 (one hour in seconds).

Error handling uses try-except blocks to catch validation errors, database errors, and token generation errors. Validation errors from Pydantic are automatically handled by FastAPI's exception handlers. Database errors are caught and converted to generic HTTP 500 responses. Token generation errors are caught and converted to HTTP 500 responses.

## Success Criteria

Successful credentials must result in HTTP 201 response with a valid JWT token. The issued token must be decodable using the same secret key and algorithm used to create it. The decoded token must contain the correct user ID in the sub claim, the correct role in the role claim, an iat timestamp matching the token generation time, and an exp timestamp one hour in the future.

Invalid email addresses must return HTTP 401 Unauthorized without distinguishing between "user not found" and "invalid password". Sending the same email address with different passwords must not reveal whether the email is registered through different error messages or response timing.

Valid credentials from different user roles must each receive appropriate tokens containing that user's specific role. An adopter account must receive a token with role "adopter", a staff account must receive a token with role "staff", and an admin account must receive a token with role "admin".

Rate limiting must prevent brute-force attacks by delaying responses after repeated failures. Three failed attempts within five minutes must result in one-second delays. Five failed attempts must result in five-second delays. Ten failed attempts must result in account lockout for fifteen minutes.

Audit logs must contain entries for all login attempts. Each successful login must be recorded with the user ID, email, timestamp, IP address, and user agent. Each failed attempt must be recorded with the attempted email, timestamp, IP address, user agent, and failure reason.

Malformed requests missing required fields must return HTTP 400 Bad Request describing which fields are missing or invalid. Requests with invalid email format must return HTTP 400 Bad Request with a validation error message.

## Testing Strategy

Unit tests should verify Pydantic schema validation for the login request. Tests should confirm that valid email and password values pass validation, that missing email returns a validation error, that missing password returns a validation error, that invalid email format returns a validation error, and that empty password values are accepted.

Integration tests should verify the complete login flow against a real database. Tests should create a user account with known credentials, then test login with the correct password, and verify that the response contains a valid JWT token with the correct claims. Tests should then attempt login with the wrong password and verify that HTTP 401 is returned. Tests should attempt login with an email that does not exist in the database and verify that HTTP 401 is returned without distinguishing from wrong password. Tests should verify that the response includes token_type set to "Bearer" and expires_in set to 3600.

Rate limiting tests should verify that three failed login attempts within five minutes result in one-second delays, that five failed attempts result in five-second delays, and that ten failed attempts lock the account for fifteen minutes. Tests should verify that successful login clears the rate limiting counter for that user.

Audit logging tests should verify that successful login attempts are logged with correct user ID, email, timestamp, IP address, and user agent. Tests should verify that failed login attempts are logged with the attempted email, timestamp, IP address, user agent, and failure reason.

Security tests should verify that password values in the request body are never logged or exposed in error messages. Tests should verify that timing differences between valid and invalid email addresses are minimal and that rate limiting is applied consistently regardless of whether the email is registered.

Token validation tests should verify that issued tokens can be decoded using the configured secret key and algorithm, that token claims are correct, and that tokens expire after one hour.

## Acceptance Checklist

- [ ] Login endpoint accepts POST requests with email and password
- [ ] Email addresses are validated with RFC standard email format
- [ ] Password comparison uses bcrypt verification against stored hash
- [ ] HTTP 401 Unauthorized returned for invalid credentials without distinguishing invalid email from invalid password
- [ ] HTTP 400 Bad Request returned for malformed requests with validation error description
- [ ] Successful login issues JWT token with HS256 signature
- [ ] JWT token includes sub claim with user UUID, role claim with user role, iat claim, and exp claim
- [ ] Token expiration time set to one hour from issuance
- [ ] HTTP 201 Created status returned for successful authentication
- [ ] Response includes token, token_type "Bearer", and expires_in 3600
- [ ] Rate limiting implemented with delays after three, five, and ten failed attempts
- [ ] Account lockout for fifteen minutes after ten failed attempts within five-minute window
- [ ] All authentication attempts recorded in audit log with timestamp, IP address, user agent, and user ID or email
- [ ] No timing attacks possible through response time differences between registered and unregistered email addresses
