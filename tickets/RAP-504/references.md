# RAP-504 References

## Files Created
- `src/db/alembic/versions/038_add_oauth_columns_to_users.py` — Migration
- `src/schemas/oauth.py` — Pydantic schemas
- `src/services/google_oauth_service.py` — Google API service
- `src/api/google_oauth.py` — FastAPI router
- `frontend/src/app/login/page.tsx` — Login page
- `frontend/src/app/auth/google/callback/page.tsx` — Callback handler
- `tests/unit/test_google_oauth_service.py` — Service tests
- `tests/unit/test_google_oauth_api.py` — API/schema tests

## Files Modified
- `src/db/models/user.py` — Added OAuth columns
- `src/config.py` — Added Google OAuth settings
- `src/schemas/user.py` — Added oauth_provider, profile_picture_url to response
- `src/api/auth.py` — Reject OAuth-only users on password login
- `src/app.py` — Register google_oauth_router
