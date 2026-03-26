---
task: T03
story: S01
epic: EPIC-1
title: Implement seed data for testing
status: ready
priority: medium
agent_type: backend
created: 2026-03-25T17:13:26.725743
---

# T03: Implement seed data for testing

## Description

Create SQL seed data for the animals table with realistic Paraguayan animal shelter data. Seeds are used for local development and integration tests — they must be idempotent (safe to run multiple times) and representative of real data scenarios including edge cases.

## Context

- Animals table schema defined in S01/T01 (must exist before running seeds)
- Seed file goes in `supabase/seed.sql` — auto-applied by `supabase db reset`
- Include animals in all possible statuses: available, reserved, adopted, medical hold, deceased
- Use realistic Paraguayan names and locations (Asunción, Luque, San Lorenzo, etc.)
- EU donor context: include animals with compelling stories for fundraising

## Seed file to create

Create or append to `supabase/seed.sql`:

```sql
-- ============================================================
-- SEED: Animals table — Refugio Animal Paraguay
-- Idempotent: uses ON CONFLICT DO NOTHING
-- Run with: supabase db reset (local) or supabase db push (remote)
-- ============================================================

-- Truncate for clean dev environment (remove for production seeds)
-- TRUNCATE TABLE animals RESTART IDENTITY CASCADE;

INSERT INTO animals (
  id, name, species, breed, age_years, age_months,
  sex, weight_kg, status, description, intake_date,
  intake_reason, location, microchip_number, is_featured
) VALUES
  -- Available animals (showcase for adoption catalog)
  (
    'a1000000-0000-0000-0000-000000000001',
    'Toti', 'dog', 'mestizo', 3, 0,
    'male', 12.5, 'available',
    'Toti llegó al refugio en buen estado. Es cariñoso, le encanta jugar y se lleva bien con otros perros. Ideal para familias con niños.',
    '2025-11-15', 'abandoned', 'Asunción', NULL, true
  ),
  (
    'a1000000-0000-0000-0000-000000000002',
    'Luna', 'dog', 'labrador mix', 1, 6,
    'female', 8.0, 'available',
    'Luna es una perra joven y activa. Fue rescatada de la calle en Luque. Está vacunada y desparasitada. Busca una familia activa.',
    '2026-01-10', 'rescue', 'Luque', 'PY-2026-001234', true
  ),
  (
    'a1000000-0000-0000-0000-000000000003',
    'Michi', 'cat', 'mestizo', 2, 0,
    'female', 3.2, 'available',
    'Michi es una gata tranquila y afectuosa. Se adapta bien a espacios pequeños. Ideal para apartamentos.',
    '2025-12-20', 'surrendered', 'San Lorenzo', 'PY-2025-005678', false
  ),
  (
    'a1000000-0000-0000-0000-000000000004',
    'Rex', 'dog', 'rottweiler mix', 5, 0,
    'male', 28.0, 'available',
    'Rex tiene una apariencia imponente pero un corazón enorme. Entrenado en comandos básicos. Necesita dueño con experiencia.',
    '2025-09-01', 'abandoned', 'Asunción', NULL, false
  ),
  (
    'a1000000-0000-0000-0000-000000000005',
    'Nieve', 'cat', 'siamés mix', 4, 0,
    'female', 4.1, 'available',
    'Nieve es selectiva con las personas pero muy leal una vez que te acepta. No se lleva bien con otros gatos.',
    '2026-02-14', 'surrendered', 'Fernando de la Mora', NULL, false
  ),
  -- Reserved (pending adoption approval)
  (
    'a1000000-0000-0000-0000-000000000006',
    'Coco', 'dog', 'golden retriever mix', 2, 3,
    'male', 18.5, 'reserved',
    'Coco tiene proceso de adopción en curso. Muy sociable con humanos y animales.',
    '2025-10-05', 'rescue', 'Asunción', 'PY-2025-009999', false
  ),
  -- Adopted (historical data for reports)
  (
    'a1000000-0000-0000-0000-000000000007',
    'Pelusa', 'cat', 'angora mix', 1, 0,
    'female', 3.5, 'adopted',
    'Pelusa fue adoptada en enero 2026. Está en su hogar definitivo en Asunción.',
    '2025-08-20', 'abandoned', 'Asunción', NULL, false
  ),
  (
    'a1000000-0000-0000-0000-000000000008',
    'Bruno', 'dog', 'beagle', 3, 0,
    'male', 11.0, 'adopted',
    'Bruno fue adoptado por una familia holandesa radicada en Paraguay.',
    '2025-07-15', 'surrendered', 'Luque', 'PY-2025-000111', false
  ),
  -- Medical hold (edge case for status filtering)
  (
    'a1000000-0000-0000-0000-000000000009',
    'Pinta', 'dog', 'dálmata mix', 0, 8,
    'female', 5.2, 'medical_hold',
    'Pinta está recuperándose de una cirugía. Estará disponible en 3-4 semanas.',
    '2026-02-28', 'rescue', 'Capiatá', NULL, false
  ),
  -- Puppy litter (tests age display edge case: 0 years)
  (
    'a1000000-0000-0000-0000-000000000010',
    'Negrito', 'dog', 'mestizo', 0, 2,
    'male', 1.8, 'available',
    'Negrito es uno de los cachorros rescatados de una camada de 5. Muy juguetón y saludable.',
    '2026-03-01', 'rescue', 'San Lorenzo', NULL, true
  )
ON CONFLICT (id) DO NOTHING;
```

## Acceptance Criteria

- [ ] `supabase/seed.sql` created (or seed block appended if file exists)
- [ ] Seed data includes animals in all statuses: `available`, `reserved`, `adopted`, `medical_hold`
- [ ] At least 3 `available` animals are `is_featured = true` for homepage display
- [ ] At least one animal has `age_years = 0` (puppy/kitten) to test age display edge case
- [ ] At least one animal has a `microchip_number` (non-null) for search tests
- [ ] `supabase db reset` runs without errors (idempotent via `ON CONFLICT DO NOTHING`)
- [ ] IDs use predictable UUIDs (not random) so integration tests can reference them by ID
- [ ] Names and descriptions are in Spanish (Paraguayan context)

## Implementation Notes

- Use predictable UUIDs for seed data (e.g., `a1000000-0000-0000-0000-00000000000N`) — tests reference these IDs directly
- Do NOT use `gen_random_uuid()` in seed files — seeds must be deterministic
- Add animals from multiple Paraguayan cities: Asunción, Luque, San Lorenzo, Fernando de la Mora, Capiatá
- Descriptions should be adoption-appeal friendly — this data appears in the public catalog
- If `supabase/seed.sql` already has content, append this block — don't overwrite other seed data

## Related

- Depends on: S01/T01 (animals table migration)
- Depends on: S01/T02 (animals TypeScript types)
- Used by: All EPIC-1 integration tests
- Used by: Local development environment
