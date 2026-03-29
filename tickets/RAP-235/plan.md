# RAP-235 Plan

## Objective
Add TOTP secret generation and verification service as the foundation for 2FA.

## Description
Implement pyotp-based TOTP secret management: generate a secret per user, return a provisioning URI for QR codes, and verify submitted TOTP codes. This is the core backend service that all other 2FA stories depend on.

## Acceptance Criteria
- [ ] `totp_service.py` exposes `generate_secret()`, `get_provisioning_uri()`, and `verify_totp()`.
- [ ] User model has `totp_secret` (nullable) and `totp_enabled` (bool) columns.
- [ ] Alembic migration adds these columns.
- [ ] `POST /auth/2fa/setup` returns secret + provisioning URI for the authenticated user.
- [ ] `POST /auth/2fa/verify` activates 2FA after confirming the first code.
- [ ] `POST /auth/2fa/disable` deactivates 2FA (requires valid TOTP code).
- [ ] Unit tests cover service logic with 80%+ coverage.
- [ ] Integration tests cover the happy paths.

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — requires schema migration, new service, new router, and integration with login flow.

## Approach
1. Add `totp_secret` / `totp_enabled` to User model + migration.
2. Implement `src/services/totp_service.py` (pure functions, no DB access).
3. Implement `src/api/two_factor.py` router with setup/verify/disable endpoints.
4. Register router in `app.py`.
5. Add pyotp + qrcode to `pyproject.toml`.
6. Write unit + integration tests.

## Dependencies
- Depends on: RAP-007 (JWT Auth), RAP-104 (Account Lockout) — both done.

## Risks
- pyotp not in existing deps → install and add to pyproject.toml.
