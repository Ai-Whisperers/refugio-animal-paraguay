---
task_id: T01
task_title: Implement Email Verification Endpoint
task_status: pending
story_id: S02
epic_id: EPIC-10
created_date: 2026-03-25
estimated_effort: 5
dependencies:
  - EPIC-10
  - S01-user-registration-and-login
  - T01-implement-registration-endpoint (must complete first)
---

# T01: Implement Email Verification Endpoint

## Overview

The email verification endpoint is a critical security boundary that confirms a user's email ownership before granting full account access. During user registration, a unique, time-limited verification token is generated and delivered to the provided email address. This endpoint validates that token, confirms the user received and accessed their email, and transitions the account from an unverified to verified state in the database.

Email verification serves multiple protective purposes: it prevents account creation with invalid or mistyped email addresses, blocks account takeover attempts using other people's emails (since the attacker would lack access to the verification email), and ensures users maintain reliable contact information for critical notifications like password reset instructions. The endpoint must handle the common scenario where users either never receive their verification email or accidentally delete it before verifying, supporting a resend mechanism so they can request a new token without creating a duplicate account.

## Why This Task Matters

Email verification is the first line of defense against email-based account enumeration, impersonation attacks, and user confusion from typos during registration. A weak email verification flow creates multiple attack vectors: an attacker could register with someone else's email and gain account access if token validation is insufficient, compromised tokens could provide unauthorized account activation if expiration enforcement is missing, and information disclosure from error messages could reveal whether specific emails exist in the system.

From a user experience perspective, email verification is often the first interaction users have with the system after registration. A confusing, slow, or unreliable verification flow creates friction that damages adoption and trust. Conversely, a smooth flow that clearly explains the verification requirement and provides easy resend capability builds confidence in the system's professionalism and attention to user needs.

The email verification endpoint is foundational to the broader email-based security model used throughout the authentication system, including password reset flows that depend on the same token generation and validation patterns. Implementing email verification correctly establishes patterns and standards that carry through to all subsequent email-based workflows.

## Technical Requirements

The email verification endpoint accepts verification tokens from users (typically provided via a clickable link in an email) and validates them against the database. The endpoint must perform several validation steps: confirm the token exists in the database, check that the token has not expired (tokens should be valid for exactly twenty-four hours from generation), retrieve the associated user account, and verify the account is currently in an unverified state (preventing duplicate verification or verification of already-verified accounts).

Token storage in the database requires hashing for security. The verification token generated during registration is cryptographically secure random data, but storing it in plaintext in the database creates a risk: if the database is compromised, an attacker could activate any unverified account by using any token found in the database. Instead, tokens are hashed using SHA-256 before storage, and the endpoint compares a hash of the provided token against the hashed value in the database. This approach ensures that even database compromise does not leak usable tokens.

The endpoint must implement constant-time comparison when validating hashed tokens to prevent timing side channel attacks. A naive string comparison would take slightly longer when comparing a token that matches the first few characters versus one that matches nothing, allowing attackers with precise timing measurements to gradually reconstruct valid tokens. FastAPI and the Python standard library provide secure comparison functions that always take the same time regardless of where a mismatch occurs.

Once validation succeeds, the endpoint updates the user account to set an email_verified flag in the database and optionally records the verification timestamp. The database update must be atomic and use a transaction to ensure consistency. The response should be a simple success message without disclosing any sensitive information about the token or other users.

Error handling must carefully balance security with user experience. If a token is invalid or expired, the endpoint should return a generic error message indicating verification failed without specifying whether the token was malformed, expired, or never existed. This prevents attackers from using error messages to enumerate valid tokens. However, if a user provides a valid token for an account that is already verified, the endpoint should return success (idempotent behavior) rather than an error, acknowledging that the user has successfully verified their account even if this particular verification attempt is redundant.

Audit logging must record all verification attempts, including successful verifications and failures. Each audit log entry should capture the timestamp, the user account being verified (or unknown if the token is invalid), the IP address making the request, and the user agent (browser/client information). This audit trail helps detect abuse patterns like rapid failed verification attempts that might indicate token enumeration attacks.

## Implementation Approach

The verification endpoint is a public, unauthenticated route since unverified users cannot yet possess valid authentication tokens. The endpoint accepts a GET parameter or URL path segment containing the verification token. Using a path segment is more user-friendly since users typically encounter this via email links, which browsers handle more reliably than query parameters.

The implementation uses Pydantic schemas to define request parameters and response structures. The request schema validates that the token is present and is a string within reasonable length bounds. The response schema provides a success message and optionally includes information about the verification process.

Token validation uses the same SHA-256 hashing approach employed for password reset and other security-critical tokens. The implementation retrieves the unverified user account by searching for records with an email_verified flag set to false and a non-null token_hash field. If multiple matching records exist (which indicates a database integrity issue), the endpoint should log an error and return a generic failure message rather than attempting to verify one account arbitrarily.

The endpoint integrates with the audit logging system to record all verification attempts. Successful verifications are logged as informational events, while failed attempts (invalid or expired tokens) are logged as warning events to facilitate intrusion detection. The audit log captures the user ID if the token is valid, or null if the token is invalid, since verification attempts with invalid tokens might not correspond to any user account.

Email resend is handled by a separate endpoint (T02-implement-password-reset-resend, or in this case potentially an extension to S01's registration logic) that generates a new token and sends a new email. The verification endpoint itself does not resend emails; it only validates tokens that have already been distributed.

## Success Criteria

A successful email verification endpoint implementation meets the following criteria: verification tokens remain valid for exactly twenty-four hours from their generation timestamp, verification fails gracefully with a generic error message for expired tokens without revealing the expiration time or reason for failure, tokens are stored as SHA-256 hashes in the database and never stored or logged in plaintext, comparison of hashed tokens uses constant-time comparison to prevent timing attacks, successful verification updates the user account to set email_verified to true and records the verification timestamp, the endpoint is idempotent and returns success for already-verified accounts, all verification attempts are logged in the audit trail with IP address, user agent, and timestamp, the endpoint returns appropriate HTTP status codes including 200 for successful verification, 400 for malformed requests lacking a token, 404 for invalid or expired tokens (generic error without revealing reason), and 500 for server errors, the endpoint implementation uses parameterized queries to prevent SQL injection, Pydantic schema validation to reject malformed input, and proper error handling to avoid exposing sensitive information.

## Testing Strategy

The test suite for the email verification endpoint covers both happy path scenarios and edge cases. Happy path tests verify that a valid, non-expired token transitions an unverified account to verified status, updates the verification timestamp, and returns a 200 success response. Edge case tests verify that expired tokens return a generic 404 or similar error without revealing the expiration status, that tokens for already-verified accounts return success (idempotent), that malformed tokens missing the token parameter return a 400 error, that invalid token formats (too short, too long, non-alphanumeric) return a 400 error, and that tokens from one user cannot be used to verify a different user's account.

Token reuse testing verifies that after a token is used once to verify an account, the same token cannot be used again, and that the token is marked as consumed or deleted in the database. This prevents attackers who obtain old tokens from verifying multiple accounts.

Timing side channel testing uses a test harness that provides valid and invalid tokens and measures response times. The test ensures that response times are statistically identical regardless of whether a provided token matches a valid token, ensuring constant-time comparison prevents timing attacks.

Audit logging testing verifies that all verification attempts are recorded in the audit trail, that successful verifications include the correct user ID, that failed verifications record the attempt with null user ID, and that IP address and user agent information are captured correctly.

Database consistency testing verifies that the email_verified flag is correctly set to true after verification, that the verification timestamp is recorded and matches the request time within reasonable bounds (within a few seconds), and that the token record is properly handled (deleted, marked consumed, or archived).

Email delivery integration testing (if email resend is implemented as part of this task) verifies that verification tokens expire at exactly twenty-four hours and that users receive a generic expiration message if they attempt verification after that period without requesting a new token.

## Acceptance Checklist

- [ ] Email verification endpoint accepts verification tokens via URL path parameter
- [ ] Endpoint validates tokens are present and in valid format (400 for missing/malformed)
- [ ] Verification tokens are stored as SHA-256 hashes, never in plaintext
- [ ] Token comparison uses constant-time comparison to prevent timing attacks
- [ ] Tokens expire after exactly twenty-four hours from generation
- [ ] Expired tokens return generic error message without revealing expiration (404 or similar)
- [ ] Valid tokens transition unverified accounts to verified state
- [ ] Endpoint updates email_verified flag and records verification timestamp atomically
- [ ] Endpoint is idempotent for already-verified accounts (returns success)
- [ ] Endpoint returns HTTP 200 for successful verification
- [ ] Endpoint returns HTTP 400 for malformed requests
- [ ] Endpoint returns HTTP 404 or similar for invalid/expired tokens without revealing reason
- [ ] All verification attempts logged in audit trail with timestamp, IP, user agent
- [ ] Successful verifications include correct user ID in audit log
- [ ] Failed verifications record attempt with null user ID
- [ ] Implementation uses parameterized queries to prevent SQL injection
- [ ] Error messages do not disclose sensitive information or reveal system details
- [ ] One valid token cannot verify multiple accounts (token reuse prevention)
- [ ] Tokens are properly consumed/deleted after successful verification
- [ ] Database transaction ensures email_verified update is atomic and consistent
- [ ] Unit tests cover happy path, expired tokens, invalid tokens, already-verified accounts
- [ ] Integration tests verify end-to-end verification flow including audit logging
- [ ] Timing side channel tests confirm constant-time comparison
- [ ] All tests pass with zero failures
- [ ] Code passes linting and type checking
- [ ] Documentation is updated with endpoint description and error codes
- [ ] Endpoint is integrated with the application's dependency injection system
- [ ] Error responses follow the standardized error response format for the API
