---
task_id: T02
task_title: Implement Password Reset Endpoint
task_status: pending
story_id: S02
epic_id: EPIC-10
created_date: 2026-03-25
estimated_effort: 8
dependencies:
  - EPIC-10
  - S01-user-registration-and-login
  - T02-implement-login-endpoint
---

# Task: Implement Password Reset Endpoint

## Overview

The password reset endpoint implements a two-part security flow allowing users to recover account access when they have forgotten their password. This task encompasses implementation of both the password reset request endpoint (initiating the recovery flow) and the password reset completion endpoint (finalizing the new password). The password reset flow represents a critical security boundary where unauthenticated users can interact with the authentication system without exposing sensitive information about account existence or status. The endpoints must use time-limited security tokens delivered via email, prevent information disclosure that could aid attackers in enumerating valid accounts, enforce password strength validation, and provide audit trails of all reset attempts. Unlike email verification tokens which persist until consumed, password reset tokens expire after one hour, enforcing urgency and reducing the window for attackers to exploit compromised tokens.

## Why This Task Matters

Users inevitably forget passwords, and a smooth password reset flow is essential for user experience and account recovery. A weakly implemented password reset mechanism introduces multiple attack vectors: attackers can enumerate valid accounts by observing different error messages between valid and invalid users, attackers can attempt to reset victims' accounts and intercept their email flows, attackers can perform dictionary attacks against reset tokens, and poorly stored tokens can be compromised alongside the database. Strong implementation prevents these attacks while maintaining privacy, building user confidence in account security, and complying with industry best practices. The password reset flow also serves as a strong signal to users that the platform takes security seriously, influencing their perception of account safety. Failure to implement this correctly undermines the entire authentication system's security posture because password reset often becomes the weakest link users rely on when they lose access.

## Technical Requirements

### Password Reset Request Endpoint

The password reset request endpoint is an unauthenticated public route that accepts an email address and initiates the password reset flow. The endpoint accepts the user's email address via request body. Email addresses are normalized to lowercase before database lookups to prevent case-sensitivity bypasses. The endpoint always returns HTTP 200 with an identical success message regardless of whether the email address exists in the system. This generic response prevents account enumeration attacks where an attacker could discover which email addresses have accounts by observing different responses. If the email address exists in the system and the associated account is verified, the system generates a cryptographically secure reset token containing minimum thirty-two characters or one hundred twenty-eight bits of entropy using a secure random number generator. The token is hashed using SHA-256 and stored in the database along with a timestamp indicating when the token was generated. The token must never be stored in plaintext in the database; if the database is compromised, plaintext tokens would allow immediate account takeover. The system sends an email to the requesting address containing a reset link with the unhashed token embedded in the URL parameter, allowing users to reset their password. Email delivery happens asynchronously in the background without blocking the HTTP response, improving perceived responsiveness. The endpoint logs all reset requests in the audit trail regardless of outcome, recording the requested email address (without revealing whether it matched an account), the timestamp, the client IP address, and the user agent string. The endpoint implements rate limiting to prevent brute force attacks attempting to generate unlimited reset tokens for valid accounts; after five reset requests for the same email address within one hour, subsequent requests are rejected with HTTP 429 (Too Many Requests).

### Password Reset Completion Endpoint

The password reset completion endpoint is an unauthenticated public route that accepts a reset token and a new password, then updates the user's password if validation passes. The endpoint accepts the reset token via URL path parameter (matching the email verification endpoint pattern for consistency) and the new password via request body. The endpoint validates that the token is present and properly formatted, rejecting malformed or empty tokens with HTTP 400 (Bad Request). The token is hashed using SHA-256 and compared against stored tokens in the database using constant-time comparison to prevent timing side channel attacks. Constant-time comparison ensures response time remains identical regardless of whether the token matches, preventing attackers from inferring token validity through timing measurements. If no matching token exists or the matching token has expired (tokens expire one hour after generation), the endpoint returns a generic HTTP 404 (Not Found) error message without revealing the specific failure reason. This generic error prevents attackers from distinguishing between invalid tokens, expired tokens, and tokens for non-existent accounts. The endpoint validates the new password meets strength requirements: minimum twelve characters in length, containing at least one uppercase letter, at least one lowercase letter, at least one digit, and at least one special character from the set of common symbols. If the password fails validation, the endpoint returns HTTP 400 with a specific error message describing which requirements are not met, allowing users to correct the password. The endpoint prevents users from resetting their password to the same password they previously used by comparing the new password's bcrypt hash against the user's current password hash; if the hashes match, the endpoint rejects the reset with HTTP 400 indicating the new password must be different. After successful password reset, the user's password hash is updated in the database with the new password hashed using bcrypt at cost factor minimum twelve. All tokens for that user are immediately revoked by deleting all existing reset tokens, preventing any other tokens from being used to reset the password again. The endpoint sends an optional confirmation email to the user notifying them that their password was successfully reset, providing evidence if the reset was unauthorized (though the user has already authenticated by possessing the reset token). The endpoint logs the reset completion attempt in the audit trail with the username (now known from the token), timestamp, success or failure status, and failure reason if applicable. The endpoint invalidates any active JWT tokens issued to that user by incrementing a token revocation counter in the user's account record; this ensures that if an attacker had stolen a token before the password reset, that token becomes invalid immediately. The endpoint implements rate limiting to prevent brute force attacks attempting to guess reset tokens; after ten failed reset attempts from the same IP address within one hour, subsequent reset attempts are rejected with HTTP 429 for fifteen minutes.

### Token Generation and Storage

Reset tokens are generated using Python's `secrets` module or equivalent cryptographically secure random source, producing tokens of minimum thirty-two characters or one hundred twenty-eight bits of entropy. Tokens are generated as random alphanumeric strings suitable for embedding in email URLs. Before storage in the database, tokens are hashed using SHA-256 producing a fixed-length hash suitable as a database column. The original unhashed token is returned to the endpoint caller and embedded in the reset email link. The reset token table maintains columns for user_id, token_hash (the SHA-256 hash), created_at (timestamp), and expires_at (timestamp set to one hour after creation). Tokens do not need to be explicitly deleted on expiration; the endpoint simply rejects tokens where the current time exceeds expires_at. At password reset completion, all tokens for the user are deleted to prevent other tokens from being used after the user has reset their password.

### Information Disclosure Prevention

The password reset request endpoint returns identical success messages regardless of account existence. The password reset completion endpoint uses generic error messages for expired or invalid tokens without distinguishing between the two. The endpoint does not reveal whether an account is verified or unverified, whether the email address exists, or any other account status information. Error messages for password validation failures are specific and helpful to legitimate users but do not reveal information useful for attacks. The endpoint logs full details in the audit trail for operations staff but returns minimal information to the client.

### Database Consistency and Transactions

The password reset completion endpoint updates both the password hash and the token revocation counter in a single atomic transaction, ensuring that if the operation partially fails, neither update takes effect. The token lookup query includes the expiration check in the WHERE clause, ensuring expired tokens are never returned. All database operations use parameterized queries to prevent SQL injection attacks.

### Integration with Existing Systems

The password reset endpoints integrate with the email delivery system to send reset and confirmation emails asynchronously. The endpoints integrate with the audit logging system to record all attempts. The endpoints integrate with the JWT token system to invalidate existing tokens on successful password reset. The endpoints use the same Pydantic validation schemas and error response formats as other authentication endpoints for consistency.

## Implementation Approach

The password reset request endpoint is implemented as a public unauthenticated route on the authentication router. The route accepts an email address in the request body. The handler normalizes the email to lowercase, generates a secure reset token, hashes the token using SHA-256, stores the token in the reset_tokens database table, sends the reset email asynchronously, and returns a generic success response. The handler uses FastAPI's BackgroundTasks to queue the email delivery without blocking the response.

The password reset completion endpoint is implemented as a public unauthenticated route on the authentication router. The route accepts a token via path parameter and a new password via request body. The handler validates the token format, hashes the token using SHA-256, queries the database for a matching token with current timestamp less than expiration, validates the new password meets strength requirements, hashes the new password using bcrypt at minimum cost factor twelve, updates the user's password and revocation counter in an atomic transaction, deletes all tokens for the user, sends a confirmation email asynchronously, and returns a success response. The handler uses Pydantic schemas to validate the password format before processing.

Both endpoints implement rate limiting using a decorator or middleware that tracks request counts per email address (for the request endpoint) or per IP address (for the completion endpoint) in Redis, rejecting requests that exceed thresholds within time windows.

Both endpoints log all attempts in the audit logging system with appropriate context information.

## Success Criteria

The password reset request endpoint returns HTTP 200 with identical message for valid and invalid email addresses. The endpoint generates tokens containing minimum one hundred twenty-eight bits of entropy. Tokens are stored as SHA-256 hashes in the database, never as plaintext. Reset emails are delivered asynchronously within five seconds of the request. The password reset completion endpoint returns HTTP 200 on successful password update. The endpoint returns HTTP 400 for malformed or missing tokens. The endpoint returns generic HTTP 404 for expired or invalid tokens without revealing reason. The endpoint returns HTTP 400 for passwords failing strength validation. The endpoint returns HTTP 400 for passwords matching the user's current password. Tokens are valid exactly one hour after generation. Tokens are deleted after successful use. Constant-time comparison is used for token validation, with identical response times for valid and invalid tokens measurable only through statistical analysis of multiple requests. All password reset attempts are logged with user identification, timestamp, IP address, and user agent. Rate limiting rejects requests exceeding thresholds with HTTP 429. JWT tokens previously issued to the user are invalidated after password reset. Password strength validation enforces minimum twelve characters, at least one uppercase letter, at least one lowercase letter, at least one digit, and at least one special character. New passwords must be different from the user's current password. Confirmation emails are sent on successful reset.

## Testing Strategy

Happy path tests for the password reset request endpoint verify that valid email addresses for verified accounts return HTTP 200 with success message. Happy path tests for the password reset completion endpoint verify that valid non-expired tokens reset the password and return HTTP 200. Tests verify that tokens sent in confirmation emails are usable for multiple attempts as long as they have not expired (tokens are not consumed on first use, only on successful password change). Tests verify that passwords meeting all strength requirements are accepted. Tests verify that confirmation emails are sent on successful password reset.

Edge case tests verify that non-existent email addresses return the same HTTP 200 success message as valid accounts. Tests verify that unverified accounts do not receive reset emails and cannot reset their passwords. Tests verify that expired tokens return generic HTTP 404 without revealing expiration. Tests verify that tokens for non-existent accounts or wrong users cannot reset passwords. Malformed tokens (missing, empty, or wrong format) return HTTP 400. Tests verify that invalid passwords (too short, missing uppercase, missing lowercase, missing digit, missing special character) return HTTP 400 with appropriate validation message.

Token reuse tests verify that the same token cannot reset a password twice; the first reset succeeds and consumes the token, the second attempt returns HTTP 404. Tests verify that all other tokens for the user are invalidated after successful password reset; if the user received multiple reset emails, only the first one used succeeds and invalidates all others. Tests verify that reset tokens are specific to the requesting user; a token generated for one user cannot reset a different user's password.

Timing side channel tests verify that response times are identical for valid and invalid tokens, with measurable differences only appearing across many statistical samples. Tests verify that timing is identical for expired and invalid tokens.

Rate limiting tests verify that five reset requests for the same email address within one hour succeed, but the sixth request is rejected with HTTP 429. Tests verify that after hitting the rate limit, a fifteen-minute wait allows additional reset requests. Tests verify that ten failed password reset attempts from the same IP address within one hour succeed, but the eleventh is rejected with HTTP 429. Tests verify that successful resets do not count toward the brute force limit.

Audit logging tests verify that all password reset request attempts are logged with email address, timestamp, IP, and user agent. Tests verify that successful password reset completions are logged with user identification, timestamp, and success status. Tests verify that failed password reset attempts are logged with user identification, timestamp, and failure reason.

Password validation tests verify that new passwords cannot match current passwords. Tests verify that password strength validation is enforced before database updates. Tests verify that special character validation accepts the common set of symbols.

Database consistency tests verify that successful password resets update the password hash correctly. Tests verify that the token revocation counter is incremented. Tests verify that all reset tokens for the user are deleted. Tests verify that JWT token invalidation logic prevents previously-issued tokens from authenticating. Tests verify that if password reset fails partway through, neither password nor revocation counter is updated (transaction rollback).

Email delivery tests verify that reset emails are sent asynchronously in the background. Tests verify that confirmation emails are sent on successful password reset. Tests verify that emails are not sent on failed reset attempts.

## Acceptance Checklist

- [ ] Password reset request endpoint implemented as public unauthenticated route
- [ ] Endpoint accepts email address via request body
- [ ] Email addresses are normalized to lowercase before lookup
- [ ] Endpoint returns HTTP 200 with identical message for valid and non-existent accounts
- [ ] Secure reset tokens generated with minimum one hundred twenty-eight bits entropy
- [ ] Tokens are hashed using SHA-256 before storage in database
- [ ] Tokens stored in reset_tokens table with user_id, token_hash, created_at, expires_at
- [ ] Reset tokens expire one hour after generation
- [ ] Reset emails sent asynchronously via BackgroundTasks
- [ ] Reset email includes unhashed token in link
- [ ] Reset request attempts logged in audit trail with email and no account disclosure
- [ ] Rate limiting implemented: five requests per email per hour
- [ ] Password reset completion endpoint implemented as public unauthenticated route
- [ ] Token accepted via URL path parameter
- [ ] New password accepted via request body
- [ ] Malformed or missing tokens return HTTP 400
- [ ] Expired or invalid tokens return generic HTTP 404
- [ ] Token validation uses constant-time comparison
- [ ] Password strength validation enforced: minimum twelve characters, uppercase, lowercase, digit, special character
- [ ] New password validated to be different from current password
- [ ] HTTP 400 returned for passwords failing validation
- [ ] Successful reset updates password hash with bcrypt cost factor minimum twelve
- [ ] All reset tokens deleted after successful reset
- [ ] JWT token revocation counter incremented after reset
- [ ] Confirmation email sent asynchronously on successful reset
- [ ] Password reset attempts logged with user, timestamp, status, failure reason
- [ ] Rate limiting implemented: ten failed attempts per IP per hour, fifteen-minute lockout
- [ ] Password reset completion accepts only one password change per token per hour
- [ ] All queries use parameterized statements preventing SQL injection
- [ ] Pydantic validation schemas defined for request/response
- [ ] Error messages match standard authentication error format
- [ ] Logging integration with audit system complete
- [ ] Email integration with async delivery system complete
- [ ] Unit tests cover happy path, edge cases, token reuse, timing side channels
- [ ] Integration tests cover email delivery, database updates, transaction consistency
- [ ] Rate limiting tests verify thresholds and reset periods
- [ ] Audit logging tests verify all attempts recorded
- [ ] All code linted with zero warnings
- [ ] All code type-checked with zero type errors
- [ ] Documentation updated with password reset flow
- [ ] Pull request includes test results demonstrating coverage above ninety percent
