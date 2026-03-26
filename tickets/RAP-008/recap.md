# RAP-008 Recap

## Outcome
Delivered full animal photo gallery support. All planned components implemented and committed.

## Acceptance Criteria — Final Status
- [x] primary_photo_url nullable TEXT column on animals
- [x] animal_photos table with id, animal_id FK, url, caption, display_order, created_at
- [x] Alembic migration 003 (upgrade + downgrade)
- [x] AnimalResponse includes primary_photo_url and photos list ordered by display_order asc, created_at asc
- [x] POST /animals/{id}/photos — staff only, returns 201
- [x] DELETE /animals/{id}/photos/{photo_id} — staff only, returns 204
- [x] PATCH /animals/{id} accepts primary_photo_url
- [x] 18 integration tests covering CRUD, ordering, auth enforcement, wrong-animal protection, cascade delete
- [x] All 178 tests passing, 0 failing
- [x] Pyright 0 errors

## Key Learnings
- Define related models before the model that references their columns in `order_by` (can't use string-based order_by for relationship `order_by` in SQLAlchemy)
- `lazy="selectin"` is the standard pattern for async SQLAlchemy relationships — issues a second SELECT batching all IDs efficiently

## Validation Evidence
- Tests: 178 passing, 0 failing
- Pyright: 0 errors, 0 warnings
- Commit: 944cb9c
