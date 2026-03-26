# RAP-015 References

## Story
- `planning/epics/EPIC-11-public-portal/stories/S01-animal-browsing-and-search/STORY.md`

## Key Files
- `src/db/models/animal.py` — Animal/AnimalPhoto models
- `src/api/animals.py` — Existing authenticated CRUD router
- `src/schemas/animal.py` — Existing Pydantic schemas
- `src/api/public_animals.py` — NEW public browsing router
- `src/schemas/public_animal.py` — NEW public schemas with pagination

## Related Tickets
- RAP-003, RAP-004 (Animal CRUD) — dependencies, delivered
