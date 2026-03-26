# RAP-007 References

## Key Files
- `src/db/models/user.py` — User ORM model (to create)
- `src/db/alembic/versions/002_create_users_table.py` — migration (to create)
- `src/auth/utils.py` — password hash + JWT encode/decode (to create)
- `src/auth/dependencies.py` — FastAPI dependencies (to create)
- `src/api/auth.py` — auth router (to create)
- `src/config.py` — add SECRET_KEY, ALGORITHM, token expiry
- `src/api/animals.py` — add require_staff to mutations
- `src/api/adopters.py` — add require_staff to mutations
- `src/api/adoption_requests.py` — add require_staff to mutations

## Related Tickets
- RAP-004: Animals CRUD (mutations to protect)
- RAP-005: Adopters CRUD (mutations to protect)
- RAP-006: Adoption Requests workflow (mutations to protect)
