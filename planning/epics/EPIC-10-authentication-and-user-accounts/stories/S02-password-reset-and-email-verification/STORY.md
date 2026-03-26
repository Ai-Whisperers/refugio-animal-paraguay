---
story_id: S02
story_title: Password Reset and Email Verification
story_status: pending
epic_id: EPIC-10
created_date: 2026-03-25
estimated_effort: 13
dependencies:
  - S01-user-registration-and-login
---

# Story S02: Password Reset and Email Verification

## Overview

This story covers two critical security processes that protect user accounts and verify ownership of email addresses. The password reset flow allows users who have forgotten their credentials to regain access to their accounts through a secure email-based verification process. The email verification flow ensures that users own the email addresses they provide during registration and prevents abuse of the system through disposable or non-existent email addresses.

Both flows rely on time-limited security tokens that are generated, stored, and validated through the authentication system. These tokens serve as a secure intermediate credential that proves a user's ownership of an email address without requiring them to possess their password. The email verification process typically occurs during user registration, requiring users to confirm their email address before their account is fully activated. The password reset process occurs when users can no longer access their accounts and need a way to restore access.

Together, these two flows establish trust in the email addresses associated with user accounts and provide secure recovery mechanisms that maintain system security while ensuring legitimate users can regain access when needed.

## Why This Story Matters

Email verification is a fundamental security practice that prevents multiple categories of abuse. Without email verification, attackers could register accounts using email addresses they do not own, potentially impersonating legitimate users or creating accounts under false identities. Email verification ensures that the email address in the system actually belongs to the person who registered the account. This creates accountability in the system and ensures that critical communications about account changes, password resets, and donation confirmations reach the correct person.

Password reset mechanisms are essential for user experience and account recovery. Users regularly forget passwords, and without a secure password reset mechanism, they would be locked out of their accounts permanently. However, password reset is also a high-value attack target because a compromised password reset flow allows attackers to take over any account without knowing the current password. The implementation must carefully balance usability with security, ensuring that legitimate users can reset their passwords while preventing attackers from using password reset to compromise accounts belonging to other users.

The authentication system's reputation depends heavily on how well these flows are implemented. A weak password reset mechanism can undermine all other security measures in the system. If attackers can compromise accounts through password reset, then strong passwords and secure login endpoints provide little protection. Similarly, if email verification is not enforced, the email addresses in the system become unreliable, making it difficult to communicate securely with users.

## Story Description

The password reset and email verification story encompasses four distinct flows: initial email verification during user registration, resending verification emails to users who did not receive the first email, password reset initiation when users have forgotten their credentials, and password reset completion when users create a new password using the reset token.

### Email Verification During Registration

When a user completes the registration process, their account is created in the database with a status of unverified. The registration endpoint generates a secure verification token and sends it to the user's email address. This token is stored in the database associated with the user's account, along with an expiration time. The token must remain valid for a reasonable period, typically between four and twenty-four hours, allowing users time to check their email and click the verification link.

The verification token itself is a randomly generated string that is cryptographically secure and sufficiently long to prevent guessing attacks. The token is not a JWT or other structured token; it is a simple opaque string that serves as a lookup key in the database. This approach separates the concern of email verification from the concern of authentication, keeping the verification flow simple and easy to audit.

When a user receives the verification email and clicks the verification link, they are directed to a verification endpoint that accepts the token as a parameter. The endpoint looks up the token in the database to find the associated user account, validates that the token has not expired, and marks the account as verified. The token is then deleted from the database to prevent reuse.

### Resending Verification Emails

Users sometimes do not receive verification emails due to spam filter misconfiguration, email service delays, or user error. The system must provide a way for users to request a new verification email without requiring them to register a new account. This is typically exposed through an endpoint that accepts the user's email address and generates a new verification token, sending it to the provided email address.

This endpoint must be careful not to leak information about which email addresses have accounts in the system. If the endpoint responds differently for registered and unregistered email addresses, attackers can use it to enumerate valid accounts. Instead, the endpoint should respond with the same generic success message regardless of whether the email address is registered, informing the user that if an account exists with that email address, a verification email will be sent.

### Password Reset Initiation

When a user visits the password reset page and provides their email address, the password reset flow is initiated. Similar to the resent verification endpoint, this endpoint must not leak information about whether an email address has an account. It generates a time-limited password reset token, stores it in the database, and sends an email to the provided address containing a link with the token.

Password reset tokens must be kept distinct from email verification tokens in the implementation, even though they follow similar patterns. A password reset token should not also serve as an email verification token, and vice versa. This separation ensures that the security properties of each flow remain clear and prevents subtle bugs where a user could exploit one flow to bypass security controls in another.

### Password Reset Completion

When a user receives the password reset email and clicks the reset link, they are directed to a password reset completion page. This page accepts the reset token along with a new password from the user. The reset endpoint validates the token, ensures it has not expired, and then updates the user's password in the database using bcrypt hashing with the same security parameters as the initial registration.

After the password is successfully reset, the reset token is deleted from the database to prevent reuse. The user is then redirected to the login page and can authenticate with their new password.

## Acceptance Criteria

- Users who complete registration receive a verification email within five minutes of submission
- Verification emails contain a secure token that is valid for exactly twenty-four hours
- Users can verify their email address by providing the verification token to the verification endpoint
- After email verification, users can authenticate using the login endpoint
- Accounts with unverified emails are rejected by the login endpoint with an appropriate error message
- Users can request a resent verification email by providing their email address
- The resent verification endpoint does not reveal whether an email address is registered
- Users can initiate password reset by providing their email address
- Password reset emails are sent within five minutes of initiation
- Password reset tokens are valid for exactly one hour
- Users can complete password reset by providing a valid token and a new password
- Password reset tokens cannot be reused after password reset is completed
- Password reset properly validates the new password using the same requirements as initial registration
- All password resets are logged in the audit trail with timestamp and user identification
- All email verification actions are logged in the audit trail with timestamp and user identification

## Technical Considerations

Email verification and password reset tokens must be generated using a cryptographically secure random number generator. The tokens must be sufficiently long to prevent brute-force guessing; a minimum of thirty-two characters or one hundred twenty-eight bits of entropy is recommended. These tokens should be stored in the database using a hash function (such as SHA-256) rather than storing the plaintext token. This ensures that if the database is compromised, attackers cannot use the tokens to reset passwords.

The email delivery mechanism must be asynchronous, using a background task system such as Celery or FastAPI's BackgroundTasks. If email delivery is synchronous and the email service is slow or unavailable, the registration and password reset endpoints will timeout, providing a poor user experience. Using background tasks allows the endpoint to return a response to the user immediately while email delivery continues in the background.

Email addresses in the system must be stored in lowercase and compared case-insensitively. Email addresses are case-insensitive according to the Simple Mail Transfer Protocol standard, and treating them as case-sensitive creates confusion and security issues. A user who registers as user@example.com and then tries to reset the password for User@Example.Com should receive a password reset email, not an error message stating that the account does not exist.

Token expiration times must be enforced at the database level by storing an expiration timestamp with each token. When a user provides a token, the system must check that the current time is before the expiration time. Tokens with past expiration times must be rejected even if the token string itself is valid.

Password reset and email verification flows must be carefully audited to ensure they do not create timing side channels. For example, checking whether an email address exists in the system takes slightly different time depending on the database state and may allow attackers to enumerate valid accounts. These timing differences should be minimized by adding constant-time delays to responses.

## Risks and Mitigations

The primary risk in password reset and email verification is unauthorized account takeover through exploitation of the reset flow. If attackers can obtain password reset tokens, they can change user passwords and take over accounts. Mitigations include generating sufficiently long tokens, storing hashed tokens in the database, expiring tokens after a short period, and sending notifications to users when their password is reset.

Another risk is email delivery reliability. If password reset or verification emails are not delivered due to spam filtering, network issues, or email service outages, legitimate users are locked out of their accounts. Mitigations include implementing a resend mechanism, using reputable email delivery services with high deliverability rates, and monitoring email delivery metrics.

A third risk is user confusion about the difference between password reset and password change. Some users might expect to be able to change their password while logged in without going through an email verification step. The system should support both flows, allowing authenticated users to change their password directly and providing the email-based reset flow for users who have forgotten their password.

## Dependencies

This story depends on S01-user-registration-and-login. Email verification and password reset flows require that the user registration and login endpoints already exist and that the user database schema is properly set up with email fields and account status tracking.

## Story Points

This story is estimated at thirteen points, reflecting the moderate complexity of implementing secure email-based recovery flows, the importance of proper error handling and information disclosure prevention, the need for comprehensive audit logging, and the testing required to ensure the flows work correctly across different failure modes.
