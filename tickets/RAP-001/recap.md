# RAP-001 Recap

## Outcome

Delivered the core PostgreSQL schema for Refugio Animal Paraguay as Alembic migrations. Three tables created (animals, adopters, adoption_requests) with all required constraints and indexes. Seed data migration provides 5 animals and 2 adopters for development/staging.

## Acceptance Criteria — Final Status

- [x] `animals` table: id, name, species, status (CHECK), birth_date, description, created_at, updated_at — DONE
- [x] `adopters` table: id, full_name, email (unique + CHECK), phone, address, gdpr_consent_at, deleted_at, created_at, updated_at — DONE
- [x] `adoption_requests` table: id, animal_id (FK), adopter_id (FK), status (CHECK), submitted_at, decided_at, notes — DONE
- [x] EXCLUDE constraint: `uq_adoption_requests_one_pending_per_animal` via GIST prevents duplicate pending requests per animal — DONE
- [x] Indexes: animals(status), animals(created_at), adopters(email), adopters(created_at), adoption_requests(animal_id, adopter_id, status, created_at) — DONE
- [x] Alembic migration `001_create_core_animal_adoption_tables.py` created with named constraints and FK-aware downgrade — DONE
- [x] Seed data migration `seed_001` creates 5 animals (all 7 status values covered) + 2 Paraguayan adopters — DONE
- [x] Schema follows Refugio conventions: UUID PKs (gen_random_uuid()), TIMESTAMPTZ, snake_case, named constraints — DONE

## Key Learnings

- EXCLUDE constraint with GIST is the cleanest way to enforce one-pending-per-animal at the DB level — no application-layer lock needed
- Alembic seed migrations (revision chain `seed_001 → 001`) keep seed data version-tracked alongside schema
- `datetime.utcnow()` is deprecated in Python 3.12 — use `datetime.now(timezone.utc)`

## Follow-Up Actions

- [ ] RAP-002: SQLAlchemy 2.x ORM models for animals, adopters, adoption_requests
- [ ] RAP-00X: Run migrations against refugio_dev once PostgreSQL is provisioned
- [ ] RAP-00X: Consider adding `updated_at` trigger (currently must be set at application layer)

## Validation Evidence

- Migration reviewed line by line: all columns, constraints, indexes, downgrade order correct
- Seeds reviewed: 5 animals span all non-terminal status values, 2 adopters have Paraguayan addresses and GDPR consent timestamps
- Dead code removed from seeds file before commit (unused `stmt`, redundant import, deprecated datetime method)
- No live DB run available — code review only
