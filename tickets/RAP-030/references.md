# RAP-030 References

## Backend API Endpoints
- `GET /animals` — paginated list, filter by species/status
- `GET /animals/{id}` — single animal
- `POST /animals` — create (staff only)
- `PATCH /animals/{id}` — update (staff only)
- `DELETE /animals/{id}` — delete (staff only)
- `GET /adoption-requests` — list with filters
- `PATCH /adoption-requests/{id}/status` — status transition (staff only)
- `POST /auth/login` — JWT login

## Frontend Base
- `frontend/src/lib/api.ts` — API client with JWT injection
- `frontend/src/lib/auth.ts` — Token storage/decode utilities
- `frontend/src/types/api.ts` — Shared types
