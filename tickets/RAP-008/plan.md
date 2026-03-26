# RAP-008 Plan

## Objective
Add photo support to animals via a `primary_photo_url` column and a separate `animal_photos` table for multiple photos.

## Description
The animal catalog is the most user-facing part of the platform — adopters browse it to find their future pet. Without photos, the catalog is unusable. This ticket adds photo URL storage (shelter uploads to Cloudinary externally; the API only stores URLs), a primary photo field for quick display, and a photos table for galleries.

## Acceptance Criteria
- [ ] `primary_photo_url` column added to `animals` table (nullable TEXT)
- [ ] `animal_photos` table: id, animal_id (FK), url, caption (nullable), display_order (int), created_at
- [ ] Alembic migration 003 adds column + creates table
- [ ] `AnimalResponse` includes `primary_photo_url` and `photos: list[PhotoResponse]`
- [ ] `POST /animals/{id}/photos` — add a photo URL (staff only)
- [ ] `DELETE /animals/{id}/photos/{photo_id}` — remove a photo (staff only)
- [ ] `PATCH /animals/{id}` — accepts `primary_photo_url` in update payload
- [ ] Photos ordered by `display_order` asc, then `created_at` asc
- [ ] Unit tests for photo schemas
- [ ] Integration tests for photo endpoints
- [ ] Zero Pyright errors

## Complexity Assessment
**Track**: Complex — new table, migration, new endpoints, modifies existing schemas and response shapes

## Approach
Phase 1: Migration (column + table)
Phase 2: ORM model + schemas
Phase 3: Photos sub-router + wire into animals router
Phase 4: Tests

## Dependencies
- Depends on: RAP-007 (auth, for staff-only photo endpoints)
