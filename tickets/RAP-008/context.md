# RAP-008 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-26

## Current Focus
Ticket closed. All acceptance criteria met.

## Technical State
- Migration 003: `primary_photo_url` column on animals + `animal_photos` table with FK cascade + index
- Model: `AnimalPhoto` defined before `Animal` in `src/db/models/animal.py` (required for `order_by` on relationship)
- `Animal.photos` uses `lazy="selectin"` for async-safe batch loading
- Schemas: `PhotoCreate`, `PhotoResponse` added; `AnimalCreate`, `AnimalUpdate`, `AnimalResponse` updated
- API: `POST /animals/{id}/photos` and `DELETE /animals/{id}/photos/{photo_id}` (staff only)
- 18 photo integration tests in `tests/integration/test_photos.py`

## Key Decisions Made
- `AnimalPhoto` before `Animal` in same file: needed to reference `AnimalPhoto.display_order` and `AnimalPhoto.created_at` directly in relationship `order_by`
- `lazy="selectin"`: async-compatible eager load — avoids MissingGreenlet; SQLAlchemy batches all photos in one query for list endpoints
- URL-only storage: client handles Cloudinary upload externally, API stores resulting URLs
