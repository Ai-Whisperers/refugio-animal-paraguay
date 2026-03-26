---
epic_id: EPIC-10
epic_title: Authentication & User Accounts
epic_status: planning
created_date: 2026-03-25
last_updated: 2026-03-25
epic_owner: Backend Team
target_release: FPUNA-2026 Wave 1
priority: critical
estimated_effort: 34 story points
---

# EPIC-10: Authentication & User Accounts

## Overview

This epic encompasses the complete implementation of user authentication, account management, and role-based access control for the Refugio Animal Paraguay platform. The authentication system forms the foundational security layer for all user interactions with the platform, enabling user registration, secure login, password recovery, email verification, and role-based authorization across all API endpoints.

The system will support three distinct user roles—adopter, staff, and admin—each with specific permissions and capabilities. The implementation leverages JWT Bearer tokens issued upon successful login, with tokens carrying claims that identify the user and their role. This approach enables stateless authentication across distributed microservices while maintaining strong security through token expiration, signature verification, and role-based access control at the endpoint level.

## Why This Epic Matters

User authentication is a critical requirement for any application handling personal data and sensitive operations. For the Refugio Animal Paraguay platform, the authentication system serves multiple essential purposes. It ensures that only legitimate users can access the platform, protects user data through secure password storage and transmission, enables role-specific features and permissions, and provides an audit trail of user activities for compliance and security monitoring.

Without a robust authentication and authorization system, the platform cannot effectively manage user accounts, restrict access to sensitive operations, or provide differentiated experiences for different user types. The three-tier role structure—adopter, staff, and admin—reflects the real-world organizational needs of the animal sanctuary, where adopters interact with the platform as external users, staff members manage day-to-day operations, and administrators maintain the system and oversee all activities.

## Target Users

The authentication system directly serves three distinct user populations. Adopters are external users who interact with the platform to browse available animals, submit adoption applications, and manage their profile information. Staff members are internal users employed by the sanctuary who process applications, manage animal records, and coordinate adoption activities. Administrators are privileged users responsible for system configuration, user management, and oversight of all platform operations.

Each user type has fundamentally different interaction patterns with the authentication system. Adopters engage with registration, login, password reset, and profile management. Staff members additionally require department-specific views and approvals. Administrators need elevated access to user management, role assignment, and security configuration.

## Scope: In Scope

This epic includes all aspects of user authentication and account management. User registration functionality encompasses account creation with email capture, password validation, and initial profile setup. Login and session management involve JWT token generation, token validation on protected endpoints, and token refresh mechanisms. Password reset and email verification enable users to recover lost passwords and confirm email addresses before account activation. User profile management allows users to view and update their information, including email address changes that trigger re-verification. Role-based access control encompasses role assignment, role validation on endpoints, and endpoint-level authorization checks. Security features include bcrypt password hashing with salting, JWT token signing and validation, and time-limited tokens for sensitive operations. Database schema design covers user account storage, role mappings, password history if needed, and audit logging for authentication events.

## Scope: Out of Scope

External identity providers such as OAuth2 social login or SAML-based enterprise authentication are explicitly out of scope for this epic and can be addressed in future work. Two-factor authentication (2FA) using SMS or authenticator apps is deferred to a subsequent epic. Biometric authentication is also deferred. API key-based authentication for service-to-service communication is out of scope. Third-party identity verification services are not included. Session invalidation across multiple devices is deferred. Custom username selection is not included; email serves as the unique identifier. Integration with external identity management systems is out of scope.

## Stories

This epic consists of four major stories, each addressing a critical component of the authentication and account management system. Story S01 covers user registration and login, enabling users to create accounts and authenticate with credentials. Story S02 addresses password reset and email verification, providing mechanisms for account recovery and email confirmation. Story S03 focuses on profile management, allowing users to view and modify their account information. Story S04 implements role-based access control, ensuring that endpoints enforce appropriate authorization based on user roles.

## Dependencies

The authentication system depends on the successful implementation of the core API infrastructure, including FastAPI setup, asynchronous request handling, dependency injection, and error handling middleware. The database layer must be fully operational, including PostgreSQL connectivity, SQLAlchemy ORM configuration, and Alembic migration tooling. Email delivery infrastructure must be established to support verification and password reset messages. The project configuration must define security settings including JWT secret key, token expiration periods, and password requirements. Environmental configuration must provide database credentials, email service credentials, and other sensitive configuration in a secure manner.

## Success Metrics

Authentication functionality is considered successful when the registration endpoint creates user accounts with valid email addresses and hashed passwords, the login endpoint issues valid JWT tokens upon correct credentials, and the token validation fails appropriately for invalid tokens. Email verification is successful when users cannot activate accounts until email confirmation, and password reset initiates a secure token-based recovery flow. Profile management succeeds when users can retrieve their profile, update information, and trigger email re-verification on email changes. Role-based access control succeeds when endpoints correctly enforce role requirements and reject requests from unauthorized roles.

Security metrics include that passwords are stored using bcrypt hashing with computational cost factor of at least twelve, JWT tokens are signed with a strong secret key and expire within a reasonable time window, and all authentication events are logged for audit purposes. Performance metrics indicate that login requests complete within 500 milliseconds, token validation adds negligible overhead to protected endpoints, and the system handles concurrent authentication requests without timeouts. Coverage metrics require that authentication tests achieve at least 85% code coverage with tests for success paths, error cases, edge cases, and security scenarios.

## Risk Factors

The primary technical risk involves JWT token security and implementation. If tokens are not properly signed or validated, attackers could forge tokens and gain unauthorized access. This is mitigated through using well-tested JWT libraries, strong signing keys, and comprehensive token validation on every protected endpoint. A related risk is token expiration and refresh; tokens must expire quickly enough to limit damage from token theft but refreshingly commonly enough to avoid user friction. This is managed through configuration tuning and user experience testing.

Password security presents another significant risk. Weak password hashing, insufficient salting, or inadequate cost factors could allow attackers to crack passwords efficiently. This is mitigated through mandatory use of bcrypt with minimum cost factor of twelve, which is computationally expensive enough to resist brute force attacks. Database breach risk is addressed through encryption at rest if available and principle of least privilege for database access.

Email verification and password reset flows present phishing and interception risks. Users might receive fraudulent emails or tokens might be intercepted. This is mitigated through time-limited tokens, secure token generation using cryptographic randomness, email headers that prevent spoofing, and clear user education. The risk of role-based access control bypass exists if authorization is not consistently enforced across all endpoints. This is mitigated through centralized authorization dependencies, comprehensive testing of access control, and regular security audits.

A process risk involves secure credential management. If database passwords, JWT secret keys, or email service credentials leak, the entire system is compromised. This is mitigated through environment-based configuration, secret management tools, restricted access to configuration, and regular rotation of sensitive credentials.

## Technical Notes

The authentication system is built on the FastAPI framework with async-first design principles. User credentials are transmitted over HTTPS only, with the API rejecting unencrypted connections at the transport layer. Password hashing uses bcrypt with a cost factor configured as a minimum of twelve, meaning at least two to the power of twelve iterations of hashing operations. This computational cost makes rainbow tables infeasible while keeping login response times acceptable.

JWT tokens are issued upon successful login and must be included in the HTTP Authorization header of subsequent requests using the Bearer scheme. The token payload contains the user identifier (sub claim), the user's role, the issued-at timestamp (iat claim), and the expiration timestamp (exp claim). Token expiration is configured to a reasonable value, typically 15 minutes to 1 hour, balancing security against user experience. Tokens cannot be revoked before expiration in the current implementation, so expiration periods should be conservative.

The email verification process uses a separate time-limited token distinct from the session JWT token. When users register, they receive an email with a verification link containing this token. The token is single-use and expires after a configurable period, typically 24 hours. Password reset follows an analogous pattern with its own time-limited token transmitted via email.

Role-based access control is implemented through FastAPI dependency injection. A centralized dependency function validates the JWT token, extracts the role claim, and ensures the user has sufficient privileges for the endpoint. This dependency is applied to all protected routes, ensuring consistent enforcement across the API surface. The three roles—adopter, staff, and admin—form a hierarchy where admin can access all endpoints, staff can access staff and adopter endpoints, and adopters can access only adopter endpoints. This hierarchy is enforced consistently across all authorization checks.

The database schema includes a users table with columns for unique email address, bcrypt-hashed password, verification status, created timestamp, and other profile information. A roles table or enum type defines available roles. A relationship connects users to their assigned roles. Additional audit tables may track authentication events for security monitoring and compliance purposes.

All endpoints return structured error responses indicating authentication or authorization failures. Endpoints that fail authentication return HTTP 401 Unauthorized with a message indicating invalid credentials or expired tokens. Endpoints that fail authorization return HTTP 403 Forbidden with a message indicating insufficient privileges. This distinction helps clients distinguish between authentication and authorization issues.
