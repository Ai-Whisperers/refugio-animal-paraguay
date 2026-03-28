# RAP-504 Recap

## Outcome
Google OAuth2 social login fully implemented across backend and frontend. Users can sign in with Google, and existing email-based accounts can be linked to Google credentials.

## Acceptance Criteria — Final Status
- [x] Google OAuth2 authorization URL generation — DONE
- [x] Authorization code exchange and user creation/login — DONE
- [x] Account linking flow for existing accounts — DONE
- [x] OAuth-only users rejected on password login — DONE
- [x] Frontend login page with Google button — DONE
- [x] Frontend callback page — DONE
- [x] Database migration for OAuth columns — DONE
- [x] Nullable hashed_password — DONE
- [x] CSRF protection via state parameter — DONE
- [x] Unit tests (21 tests) — DONE

## Key Learnings
- httpx Response.json() is synchronous — use MagicMock not AsyncMock for response mocking
- Account linking requires careful two-step state management
- In-memory state stores need expiry cleanup to prevent memory leaks

## Validation Evidence
- Tests: 1325 passing, 0 failing (21 new OAuth tests)
- Linting: ruff clean
- Formatting: black clean
- Type check: pyright clean (0 errors)
