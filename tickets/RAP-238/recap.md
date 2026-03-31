# RAP-238 Recap

## Outcome
Delivered 2FA enforcement at login: accounts with `totp_enabled=True` now require a valid
TOTP code or backup code at every login. Attempted logins without the second factor receive
HTTP 401 with `detail="totp_required"` so clients can show the correct prompt.

## Acceptance Criteria — Final Status
- [x] Login without `totp_code` returns HTTP 401 with `detail="totp_required"` — DONE
- [x] Login with a valid live TOTP code succeeds — DONE
- [x] Login with a valid unused backup code succeeds — DONE
- [x] Login with an incorrect code returns HTTP 401 — DONE
- [x] Integration tests cover all four branches — DONE

## Key Learnings
- Returning a specific `"totp_required"` detail (not generic `"invalid_credentials"`)
  gives the frontend enough signal to show the right prompt without leaking auth logic.

## Validation Evidence
- Tests: 28 unit tests + 7 integration tests — all passing
- Linting: ruff clean on new files
- Formatting: black clean
- Coverage: new code covered by dedicated integration test file
