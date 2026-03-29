# RAP-245 Plan

## Objective
Add SENACSA (Servicio Nacional de Calidad y Salud Animal) registration number tracking to animal records so the shelter can comply with Paraguayan animal registration requirements.

## Description
SENACSA is Paraguay's national animal health and quality service. Animals registered with the shelter require a SENACSA registration number for legal compliance. This story adds the field to the Animal model, exposes it via the API, and ensures it is searchable/filterable.

## Acceptance Criteria
- [x] `senacsa_registration_number` field added to the `animals` table via Alembic migration
- [x] Animal model updated with the new field
- [x] Schemas updated (AnimalCreate, AnimalUpdate, AnimalResponse) to include the field
- [x] Animals API allows creating/updating with the SENACSA number
- [x] GET /animals supports filtering by `senacsa_registered=true|false`
- [x] Unit tests for schema validation
- [x] Integration tests covering create/update/filter by registration status

## Complexity Assessment
**Track**: Simple Fix

**Assessment result**: Simple Fix — adding a nullable string column to an existing model, updating schemas and router, adding tests.

## Approach
1. Add Alembic migration 090 to add `senacsa_registration_number` (nullable String(100)) to `animals`
2. Update Animal ORM model with the new mapped_column
3. Update AnimalCreate, AnimalUpdate, AnimalResponse schemas
4. Update animals router: accept field on POST/PATCH, add filter on GET
5. Write unit tests (schema validation) and integration tests (CRUD + filter)

## Dependencies
- Depends on: none

## Risks
- Risk: migration conflict if another branch adds columns to animals → Mitigation: check before merging
