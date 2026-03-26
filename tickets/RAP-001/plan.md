# RAP-001 Plan

## Objective
Design and create the core PostgreSQL schema for animals, adopters, and adoption requests.

## Description
The animal schema is the foundation for the entire platform. It must support animal records
(species, status, medical history), adopter profiles, and the adoption request lifecycle.
Schema must follow Refugio conventions: UUID PKs, TIMESTAMPTZ, status enums, soft-delete via
status rather than deleted_at.

## Acceptance Criteria
- [ ] `animals` table created with: id, name, species, status enum, birth_date, description, created_at, updated_at
- [ ] `adopters` table created with: id, full_name, email (unique), phone, address, gdpr_consent_at, created_at
- [ ] `adoption_requests` table with: id, animal_id (FK), adopter_id (FK), status enum, submitted_at, decided_at, notes
- [ ] EXCLUDE constraint: one active request per animal (prevents duplicate pending requests)
- [ ] Indexes: animals(status), adoption_requests(animal_id), adoption_requests(adopter_id), adoption_requests(status)
- [ ] Alembic migration file created and named descriptively
- [ ] Seed data script creates 5 sample animals + 2 adopters
- [ ] Schema validated against Refugio conventions (UUIDs, TIMESTAMPTZ, snake_case tables)

## Complexity Assessment
**Track**: Complex Implementation

### Assessment result
Complex — affects 3 tables, multiple constraints, Alembic migration, seed data. Phased approach: schema → migration → seed.

## Approach
1. Design schema using schema-designer agent
2. Write Alembic migration
3. Write seed data script
4. Validate against conventions

## Dependencies
- Depends on: tech stack decision (resolved in ADR-001)
- Blocked by: none

## Risks
- Risk: Animal status enum design may need expansion → Mitigation: use VARCHAR with check constraint initially, migrate to proper enum once status values are stable
