# RAP-235 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-29 12:00

## Current Focus
Implementing TOTP secret generation and verification — backend service + API endpoints.

## Technical State
- Branch: feature/RAP-235-totp-secret-generation
- Files to create: src/services/totp_service.py, src/api/two_factor.py, migration
- Files to modify: pyproject.toml, src/db/models/user.py, src/app.py

## Next Steps
1. Add pyotp/qrcode to pyproject.toml
2. Extend User model with totp_secret + totp_enabled
3. Create migration
4. Implement totp_service.py
5. Implement two_factor.py router
6. Register router
7. Write tests

## Blockers
None.

## Key Decisions Made
- Using pyotp for RFC 6238 compliance
- Storing TOTP secret as nullable encrypted string on User model
- QR code URI returned as string (frontend renders QR using its own library)
